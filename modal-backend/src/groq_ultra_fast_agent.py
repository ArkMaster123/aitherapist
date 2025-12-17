"""
Ultra-Fast Voice Agent using Groq Whisper + Fastest TTS
Target: <500ms effective latency (faster than ElevenLabs!)

Components:
- STT: Groq Whisper Large v3 Turbo (216x real-time, ~631ms for 5-sec audio)
- LLM: Qwen2.5-7B via vLLM (300-500ms streaming)
- TTS: Cartesia Sonic 2.0 Turbo (40ms) OR Kokoro-82m (97ms)
"""

import modal
import asyncio
import time
import numpy as np
import io
import os
from typing import Optional

from .common import app
import modal

model_path = "/models"
model_volume_cache = modal.Volume.from_name("groq-ultra-fast-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "espeak-ng")
    .pip_install(
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "groq>=0.4.0",  # Groq SDK
        "openai>=1.0.0",  # For vLLM client
        "fastapi==0.115.5",
        "huggingface_hub==0.24.7",
        "hf_transfer==0.1.8",
        "numpy",
        "scipy",
        "soundfile",
        "websockets",
        "requests",
    )
    .run_commands(
        "pip install kokoro",  # Fallback TTS
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
    from groq import Groq
    from kokoro import KPipeline
    from openai import OpenAI
    import json
    import requests


@app.cls(
    image=image,
    gpu="A10G",  # Only needed for TTS, Groq STT is API-based
    scaledown_window=300,
    timeout=600,
    volumes={model_path: model_volume_cache},
    secrets=[modal.Secret.from_name("groq-api", create_if_missing=True)],  # GROQ_API_KEY
)
class GroqUltraFastAgent:
    @modal.enter()
    def enter(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading ultra-fast voice agent on {self.device}...")
        
        # Initialize Groq client for STT (external API service, not running in Modal!)
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment. Add it to Modal secrets.")
        
        self.groq_client = Groq(api_key=groq_api_key)
        print("✅ Groq Whisper API client initialized (external service)")
        
        # Load TTS: Try Cartesia first, fallback to Kokoro
        print("Loading TTS...")
        self.use_cartesia = os.environ.get("CARTESIA_API_KEY") is not None
        
        if self.use_cartesia:
            self.cartesia_api_key = os.environ.get("CARTESIA_API_KEY")
            print("✅ Using Cartesia Sonic 2.0 Turbo (40ms latency)")
        else:
            try:
                self.tts_pipeline = KPipeline(lang_code='a')
                self.tts_sample_rate = 24000
                print("✅ Using Kokoro-82m (97ms latency)")
            except Exception as e:
                print(f"⚠️ Kokoro load error: {e}")
                self.tts_pipeline = None
        
        # LLM: Connect to vLLM server
        vllm_url = os.environ.get("VLLM_URL", "http://localhost:8000/v1")
        self.llm_client = OpenAI(
            base_url=vllm_url,
            api_key="not-needed"
        )
        print("✅ LLM client configured")
        
        self.sample_rate = 16000  # Audio sample rate
        
    async def transcribe_audio_groq(self, audio_data: np.ndarray, audio_format: str = "wav") -> Optional[str]:
        """Transcribe audio using Groq Whisper API (external service, ~631ms for 5-sec)"""
        try:
            start_time = time.time()
            
            # Convert to int16 if needed
            if audio_data.dtype != np.int16:
                if audio_data.max() <= 1.0:
                    audio_data = (audio_data * 32767).astype(np.int16)
                else:
                    audio_data = audio_data.astype(np.int16)
            
            # Save to temporary file-like object for Groq API
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as tmp_file:
                import soundfile as sf
                sf.write(tmp_file.name, audio_data, self.sample_rate)
                tmp_path = tmp_file.name
            
            try:
                # Call Groq API (external service, not running in Modal!)
                with open(tmp_path, "rb") as audio_file:
                    transcription = self.groq_client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3-turbo",  # Fastest Groq model
                        temperature=0,
                        response_format="verbose_json",
                    )
                
                text = transcription.text
                latency = (time.time() - start_time) * 1000
                print(f"🎯 Groq API STT latency: {latency:.1f}ms")
                
                return text.strip() if text else None
                
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
                
        except Exception as e:
            print(f"Groq API STT error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def generate_llm_response(self, text: str) -> str:
        """Generate LLM response via vLLM (target: 300-500ms with streaming)"""
        try:
            start_time = time.time()
            
            response_text = ""
            stream = self.llm_client.chat.completions.create(
                model="qwen-therapist",
                messages=[
                    {"role": "system", "content": "You are a compassionate therapist. Provide brief, empathetic responses."},
                    {"role": "user", "content": text}
                ],
                max_tokens=150,
                temperature=0.7,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
            
            latency = (time.time() - start_time) * 1000
            print(f"🎯 LLM latency: {latency:.1f}ms")
            
            return response_text.strip()
            
        except Exception as e:
            print(f"LLM error: {e}")
            return "I'm sorry, I couldn't process that. Can you try again?"
    
    async def synthesize_speech_cartesia(self, text: str) -> Optional[tuple[np.ndarray, int]]:
        """Synthesize speech using Cartesia Sonic 2.0 Turbo (target: 40ms)"""
        try:
            start_time = time.time()
            
            # Cartesia API call
            response = requests.post(
                "https://api.cartesia.ai/v1/tts",
                headers={
                    "Authorization": f"Bearer {self.cartesia_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model": "sonic-2.0-turbo",
                    "voice_id": "default",  # Adjust as needed
                },
                timeout=5.0,
            )
            
            if response.status_code != 200:
                print(f"Cartesia API error: {response.status_code}")
                return None
            
            # Decode audio from response
            audio_bytes = response.content
            import soundfile as sf
            import io
            audio, sr = sf.read(io.BytesIO(audio_bytes))
            
            # Convert to int16
            if audio.dtype != np.int16:
                max_val = np.max(np.abs(audio))
                if max_val > 1.0:
                    audio = audio / max_val
                audio = (audio * 32767).astype(np.int16)
            
            latency = (time.time() - start_time) * 1000
            print(f"🎯 Cartesia TTS latency: {latency:.1f}ms")
            
            return audio.astype(np.int16), int(sr)
            
        except Exception as e:
            print(f"Cartesia TTS error: {e}")
            return None
    
    def synthesize_speech_kokoro(self, text: str) -> Optional[tuple[np.ndarray, int]]:
        """Synthesize speech using Kokoro-82m (target: 97ms)"""
        try:
            if not self.tts_pipeline:
                return None
                
            start_time = time.time()
            
            with torch.no_grad():
                audio = self.tts_pipeline.tts(text)
            
            if isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()
            
            if len(audio.shape) > 1:
                audio = audio.flatten()
            
            if audio.dtype != np.int16:
                max_val = np.max(np.abs(audio))
                if max_val > 1.0:
                    audio = audio / max_val
                audio = (audio * 32767).astype(np.int16)
            
            latency = (time.time() - start_time) * 1000
            print(f"🎯 Kokoro TTS latency: {latency:.1f}ms")
            
            return audio, self.tts_sample_rate
            
        except Exception as e:
            print(f"Kokoro TTS error: {e}")
            return None

    @modal.asgi_app()
    def web(self):
        from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
        from fastapi.middleware.cors import CORSMiddleware

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
                "stt": "Groq Whisper API (external, 216x real-time)",
                "llm": "Qwen2.5-7B (vLLM)",
                "tts": "Cartesia Sonic 2.0 Turbo (40ms)" if self.use_cartesia else "Kokoro-82m (97ms)",
            }

        @web_app.websocket("/ws")
        async def websocket(ws: WebSocket):
            await ws.accept()
            print("Groq ultra-fast voice agent WebSocket connected")
            
            audio_buffer = []
            buffer_duration = 0
            min_audio_duration = 0.5  # Process every 0.5 seconds for real-time feel
            
            try:
                while True:
                    data = await ws.receive_bytes()
                    
                    if len(data) == 0:
                        continue
                    
                    # Decode audio chunk
                    audio_chunk = np.frombuffer(data, dtype=np.int16)
                    audio_buffer.append(audio_chunk)
                    buffer_duration += len(audio_chunk) / self.sample_rate
                    
                    # Process when we have enough audio
                    if buffer_duration >= min_audio_duration:
                        full_audio = np.concatenate(audio_buffer)
                        audio_buffer = []
                        buffer_duration = 0
                        
                        total_start = time.time()
                        
                        # 1. STT: Groq (processes while user speaks!)
                        transcript = await self.transcribe_audio_groq(full_audio)
                        if not transcript:
                            continue
                        
                        await ws.send_bytes(b"\x02" + transcript.encode('utf-8'))
                        
                        # 2. LLM
                        response = await self.generate_llm_response(transcript)
                        await ws.send_bytes(b"\x03" + response.encode('utf-8'))
                        
                        # 3. TTS: Cartesia (40ms) or Kokoro (97ms)
                        if self.use_cartesia:
                            audio_output, sr = await self.synthesize_speech_cartesia(response)
                        else:
                            audio_output, sr = self.synthesize_speech_kokoro(response)
                        
                        if audio_output is not None:
                            sr_bytes = sr.to_bytes(4, byteorder='big')
                            audio_bytes = audio_output.tobytes()
                            await ws.send_bytes(b"\x01" + sr_bytes + audio_bytes)
                        
                        total_latency = (time.time() - total_start) * 1000
                        print(f"🚀 Total pipeline latency: {total_latency:.1f}ms")
                        
            except WebSocketDisconnect:
                print("WebSocket disconnected")
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                await ws.close(code=1011)

        return web_app
