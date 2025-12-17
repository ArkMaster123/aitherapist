"""
LLM + TTS Agent (Modal App)
Groq STT is handled separately in the frontend - this only does LLM + TTS

Components:
- LLM: Qwen2.5-7B via vLLM (300-500ms streaming)
- TTS: Cartesia Sonic 2.0 Turbo (40ms) OR Kokoro-82m (97ms)
"""

import modal
import asyncio
import time
import numpy as np
import os
from typing import Optional

from .common import app

model_path = "/models"
model_volume_cache = modal.Volume.from_name("llm-tts-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "espeak-ng")
    .pip_install(
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "openai>=1.0.0",  # For vLLM client
        "fastapi==0.115.5",
        "numpy",
        "scipy",
        "soundfile",
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
    from kokoro import KPipeline
    from openai import OpenAI
    import requests


@app.cls(
    image=image,
    gpu="A10G",  # For TTS
    scaledown_window=300,
    timeout=600,
    volumes={model_path: model_volume_cache},
)
class LLMTTSAgent:
    @modal.enter()
    def enter(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading LLM + TTS agent on {self.device}...")
        
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
            
            response = requests.post(
                "https://api.cartesia.ai/v1/tts",
                headers={
                    "Authorization": f"Bearer {self.cartesia_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model": "sonic-2.0-turbo",
                    "voice_id": "default",
                },
                timeout=5.0,
            )
            
            if response.status_code != 200:
                print(f"Cartesia API error: {response.status_code}")
                return None
            
            import soundfile as sf
            import io
            audio, sr = sf.read(io.BytesIO(response.content))
            
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
                "llm": "Qwen2.5-7B (vLLM)",
                "tts": "Cartesia Sonic 2.0 Turbo (40ms)" if self.use_cartesia else "Kokoro-82m (97ms)",
            }

        @web_app.post("/process")
        async def process_text(request: dict):
            """Process text: LLM → TTS"""
            text = request.get("text", "")
            if not text:
                return {"error": "No text provided"}, 400
            
            try:
                total_start = time.time()
                
                # 1. LLM
                response = await self.generate_llm_response(text)
                
                # 2. TTS
                if self.use_cartesia:
                    audio_output, sr = await self.synthesize_speech_cartesia(response)
                else:
                    audio_output, sr = self.synthesize_speech_kokoro(response)
                
                if audio_output is None:
                    return {"error": "TTS failed"}, 500
                
                total_latency = (time.time() - total_start) * 1000
                print(f"🚀 Total LLM+TTS latency: {total_latency:.1f}ms")
                
                # Return audio as base64 or bytes
                import base64
                audio_bytes = audio_output.tobytes()
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                
                return {
                    "text": response,
                    "audio": audio_b64,
                    "sample_rate": sr,
                    "latency_ms": total_latency,
                }
                
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                return {"error": str(e)}, 500

        @web_app.websocket("/ws")
        async def websocket(ws: WebSocket):
            """WebSocket for streaming: receives text, sends LLM response + TTS audio"""
            await ws.accept()
            print("LLM+TTS WebSocket connected")
            
            try:
                while True:
                    # Receive text (transcript from Groq STT)
                    data = await ws.receive_text()
                    
                    if not data or len(data.strip()) == 0:
                        continue
                    
                    total_start = time.time()
                    
                    # 1. LLM
                    response = await self.generate_llm_response(data)
                    await ws.send_bytes(b"\x03" + response.encode('utf-8'))
                    
                    # 2. TTS
                    if self.use_cartesia:
                        audio_output, sr = await self.synthesize_speech_cartesia(response)
                    else:
                        audio_output, sr = self.synthesize_speech_kokoro(response)
                    
                    if audio_output is not None:
                        sr_bytes = sr.to_bytes(4, byteorder='big')
                        audio_bytes = audio_output.tobytes()
                        await ws.send_bytes(b"\x01" + sr_bytes + audio_bytes)
                    
                    total_latency = (time.time() - total_start) * 1000
                    print(f"🚀 Total LLM+TTS latency: {total_latency:.1f}ms")
                        
            except WebSocketDisconnect:
                print("WebSocket disconnected")
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                await ws.close(code=1011)

        return web_app
