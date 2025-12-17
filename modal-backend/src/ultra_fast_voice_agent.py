"""
Ultra-Fast Voice Agent: STT → LLM → TTS Pipeline
Target: <500ms total latency (faster than ElevenLabs)

Components:
- STT: Faster-Whisper (150ms)
- LLM: Qwen2.5-7B via vLLM (300-500ms streaming)
- TTS: Kokoro-82m (97ms) - fastest open-source TTS
"""

import modal
import asyncio
import time
import numpy as np
import io
from typing import Optional

from .common import app

model_path = "/models"
model_volume_cache = modal.Volume.from_name("ultra-fast-voice-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "espeak-ng")
    .pip_install(
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "faster-whisper>=1.0.0",
        "openai>=1.0.0",  # For vLLM client
        "fastapi==0.115.5",
        "huggingface_hub==0.24.7",
        "hf_transfer==0.1.8",
        "numpy",
        "scipy",
        "soundfile",
        "websockets",
    )
    .run_commands(
        "pip install kokoro",  # Kokoro-82m TTS
    )
    .env(
        {
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "HF_HUB_CACHE": model_path,
        }
    )
)

with image.imports():
    import torch
    import os
    from faster_whisper import WhisperModel
    from kokoro import KPipeline
    from openai import OpenAI
    import json


@app.cls(
    image=image,
    gpu="A10G",
    scaledown_window=300,
    timeout=600,
    volumes={model_path: model_volume_cache},
)
class UltraFastVoiceAgent:
    @modal.enter()
    def enter(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading ultra-fast voice agent on {self.device}...")
        
        # Load STT: Faster-Whisper (optimized for speed)
        print("Loading Faster-Whisper STT...")
        self.stt_model = WhisperModel(
            "base",  # base model for speed (can use "small" for better accuracy)
            device=self.device,
            compute_type="float16" if self.device == "cuda" else "int8",
        )
        print("✅ Faster-Whisper loaded")
        
        # Load TTS: Kokoro-82m (97ms TTFB - fastest open-source)
        print("Loading Kokoro-82m TTS...")
        try:
            self.tts_pipeline = KPipeline(lang_code='a')  # American English
            self.tts_sample_rate = 24000
            print("✅ Kokoro-82m loaded")
        except Exception as e:
            print(f"⚠️ Kokoro load error: {e}, will use fallback")
            self.tts_pipeline = None
        
        # LLM: Connect to vLLM server (already deployed)
        # Get vLLM URL from environment or use default
        vllm_url = os.environ.get("VLLM_URL", "http://localhost:8000/v1")
        self.llm_client = OpenAI(
            base_url=vllm_url,
            api_key="not-needed"  # vLLM doesn't require auth
        )
        print("✅ LLM client configured")
        
        self.sample_rate = 16000  # STT sample rate
        
    def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio using Faster-Whisper (target: 150ms)"""
        try:
            start_time = time.time()
            
            # Convert to int16 if needed
            if audio_data.dtype != np.int16:
                if audio_data.max() <= 1.0:
                    audio_data = (audio_data * 32767).astype(np.int16)
                else:
                    audio_data = audio_data.astype(np.int16)
            
            # Transcribe with VAD (voice activity detection)
            segments, info = self.stt_model.transcribe(
                audio_data,
                language="en",
                vad_filter=True,  # Filter out non-speech
                vad_parameters=dict(
                    min_silence_duration_ms=250,  # Optimized for real-time
                ),
                beam_size=1,  # Faster decoding
                best_of=1,
            )
            
            # Get first segment (most likely)
            text = ""
            for segment in segments:
                text += segment.text
                break  # Just get first segment for speed
            
            latency = (time.time() - start_time) * 1000
            print(f"STT latency: {latency:.1f}ms")
            
            return text.strip() if text else None
            
        except Exception as e:
            print(f"STT error: {e}")
            return None
    
    async def generate_llm_response(self, text: str) -> str:
        """Generate LLM response via vLLM (target: 300-500ms with streaming)"""
        try:
            start_time = time.time()
            
            # Stream response from LLM
            response_text = ""
            stream = self.llm_client.chat.completions.create(
                model="qwen-therapist",  # Your fine-tuned model name
                messages=[
                    {"role": "system", "content": "You are a compassionate therapist. Provide brief, empathetic responses."},
                    {"role": "user", "content": text}
                ],
                max_tokens=150,  # Keep responses short for speed
                temperature=0.7,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
            
            latency = (time.time() - start_time) * 1000
            print(f"LLM latency: {latency:.1f}ms")
            
            return response_text.strip()
            
        except Exception as e:
            print(f"LLM error: {e}")
            return "I'm sorry, I couldn't process that. Can you try again?"
    
    def synthesize_speech(self, text: str) -> Optional[tuple[np.ndarray, int]]:
        """Synthesize speech using Kokoro-82m (target: 97ms)"""
        try:
            if not self.tts_pipeline:
                return None
                
            start_time = time.time()
            
            with torch.no_grad():
                audio = self.tts_pipeline.tts(text)
            
            # Convert to numpy
            if isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()
            
            # Ensure 1D
            if len(audio.shape) > 1:
                audio = audio.flatten()
            
            # Normalize to int16
            if audio.dtype != np.int16:
                max_val = np.max(np.abs(audio))
                if max_val > 1.0:
                    audio = audio / max_val
                audio = (audio * 32767).astype(np.int16)
            
            latency = (time.time() - start_time) * 1000
            print(f"TTS latency: {latency:.1f}ms")
            
            return audio, self.tts_sample_rate
            
        except Exception as e:
            print(f"TTS error: {e}")
            return None

    @modal.asgi_app()
    def web(self):
        from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
        from fastapi.middleware.cors import CORSMiddleware
        import os

        web_app = FastAPI()

        web_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @web_app.get("/status")
        async def status():
            return {
                "status": "ready",
                "stt": "Faster-Whisper",
                "llm": "Qwen2.5-7B (vLLM)",
                "tts": "Kokoro-82m" if self.tts_pipeline else "unavailable",
            }

        @web_app.websocket("/ws")
        async def websocket(ws: WebSocket):
            await ws.accept()
            print("Ultra-fast voice agent WebSocket connected")
            
            audio_buffer = []
            buffer_duration = 0
            min_audio_duration = 1.0  # Minimum 1 second before processing
            
            try:
                while True:
                    # Receive audio data
                    data = await ws.receive_bytes()
                    
                    if len(data) == 0:
                        continue
                    
                    # Decode Opus or handle raw PCM
                    # For now, assume raw PCM int16 at 16kHz
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    audio_buffer.append(audio_chunk)
                    buffer_duration += len(audio_chunk) / self.sample_rate
                    
                    # Process when we have enough audio
                    if buffer_duration >= min_audio_duration:
                        # Combine buffer
                        full_audio = np.concatenate(audio_buffer)
                        audio_buffer = []
                        buffer_duration = 0
                        
                        # STT → LLM → TTS pipeline
                        total_start = time.time()
                        
                        # 1. STT
                        transcript = self.transcribe_audio(full_audio)
                        if not transcript:
                            continue
                        
                        # Send transcript
                        await ws.send_bytes(b"\x02" + transcript.encode('utf-8'))
                        
                        # 2. LLM
                        response = await self.generate_llm_response(transcript)
                        
                        # Send response text
                        await ws.send_bytes(b"\x03" + response.encode('utf-8'))
                        
                        # 3. TTS
                        audio_output, sr = self.synthesize_speech(response)
                        if audio_output is not None:
                            # Send audio
                            sr_bytes = sr.to_bytes(4, byteorder='big')
                            audio_bytes = audio_output.tobytes()
                            await ws.send_bytes(b"\x01" + sr_bytes + audio_bytes)
                        
                        total_latency = (time.time() - total_start) * 1000
                        print(f"🎯 Total pipeline latency: {total_latency:.1f}ms")
                        
            except WebSocketDisconnect:
                print("WebSocket disconnected")
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                await ws.close(code=1011)

        return web_app
