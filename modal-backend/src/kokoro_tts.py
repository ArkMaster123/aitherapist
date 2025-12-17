"""
Kokoro TTS websocket server for text-to-speech with voice selection.
Based on Kokoro-82m model with support for all available voices.
"""

import modal
import time
import numpy as np

from .common import app

model_path = "/models"
model_volume_cache = modal.Volume.from_name("kokoro-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "ffmpeg", "espeak-ng")
    .pip_install(
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "kokoro",
        "fastapi==0.115.5",
        "numpy",
        "scipy",
        "soundfile",
    )
)

with image.imports():
    import torch
    from kokoro import KPipeline


@app.cls(
    image=image,
    gpu="A100",
    scaledown_window=3600,  # 1 hour = 3600 seconds (max allowed by Modal)
    timeout=600,
    volumes={model_path: model_volume_cache},
)
class KokoroTTS:
    @modal.enter()
    def enter(self):
        """Initialize the Kokoro TTS model on container startup"""
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading Kokoro-82m on {self.device}...")
            
            # Load the Kokoro pipeline (lang_code required, 'en' for English)
            self.tts_pipeline = KPipeline(device=self.device, lang_code='en')
            self.sample_rate = 24000  # Kokoro standard sample rate
            
            # Get all available voices - use safe defaults if we can't detect them
            self.available_voices = [
                "af_bella", "af_sarah", "af_sky", "af_angelica", "af_ana",
                "am_adam", "am_michael", "am_sam", "am_mitchell", "am_douglas",
                "bf_donna", "bf_emma", "bf_emily", "bf_olivia", "bf_samantha",
                "bm_antonio", "bm_anthony", "bm_george", "bm_james", "bm_robert",
            ]
            
            # Try to get actual voices from the pipeline if available
            try:
                if hasattr(self.tts_pipeline, 'get_voices'):
                    actual_voices = self.tts_pipeline.get_voices()
                    if actual_voices and isinstance(actual_voices, list) and len(actual_voices) > 0:
                        self.available_voices = actual_voices
                        print(f"Loaded {len(self.available_voices)} voices from pipeline")
                elif hasattr(self.tts_pipeline, 'voices'):
                    actual_voices = self.tts_pipeline.voices
                    if actual_voices and isinstance(actual_voices, list) and len(actual_voices) > 0:
                        self.available_voices = actual_voices
                        print(f"Loaded {len(self.available_voices)} voices from pipeline")
            except Exception as e:
                print(f"Warning: Could not get voice list from pipeline: {e}. Using defaults.")
            
            print(f"✅ Kokoro-82m loaded successfully. Sample rate: {self.sample_rate}")
            print(f"Available voices: {len(self.available_voices)}")
            
            # Verify the pipeline works with a test generation
            try:
                test_audio, _ = self._generate_audio_internal("test", self.available_voices[0])
                print(f"✅ Test generation successful: {len(test_audio)} samples")
            except Exception as e:
                print(f"⚠️ Test generation failed: {e}. Service may have issues.")
                
        except Exception as e:
            print(f"❌ CRITICAL: Failed to initialize Kokoro TTS: {e}")
            import traceback
            traceback.print_exc()
            # Set safe defaults so the service can at least start
            self.device = "cpu"
            self.tts_pipeline = None
            self.sample_rate = 24000
            self.available_voices = ["af_bella"]
            raise  # Re-raise to fail fast during initialization

    def _generate_audio_internal(self, text: str, voice: str):
        """Internal method to generate audio - called by public method"""
        if self.tts_pipeline is None:
            raise RuntimeError("Kokoro pipeline not initialized")
            
        # Use default voice if not specified or invalid
        if not voice or voice not in self.available_voices:
            voice = self.available_voices[0]
        
        # Generate audio
        with torch.no_grad():
            audio = self.tts_pipeline.generate(
                text=text,
                voice=voice,
            )
        
        # Convert to numpy array if needed
        if isinstance(audio, torch.Tensor):
            audio = audio.cpu().numpy()
        
        # Ensure it's a 1D array
        if len(audio.shape) > 1:
            audio = audio.flatten()
        
        # Normalize audio to int16 range
        if audio.dtype != np.int16:
            # Normalize to [-1, 1] range if needed
            max_val = np.max(np.abs(audio)) if len(audio) > 0 else 1.0
            if max_val > 1.0 and max_val > 0:
                audio = audio / max_val
            # Convert to int16
            audio_int16 = (audio * 32767).astype(np.int16)
        else:
            audio_int16 = audio
        
        return audio_int16, self.sample_rate

    def generate_audio(self, text: str, voice: str = None):
        """Generate audio from text using Kokoro"""
        try:
            start_time = time.time()
            
            if not text or len(text.strip()) == 0:
                raise ValueError("Text cannot be empty")
            
            audio_int16, sample_rate = self._generate_audio_internal(text, voice)
            
            latency = (time.time() - start_time) * 1000
            print(f"🎯 Kokoro TTS latency: {latency:.1f}ms, voice: {voice or self.available_voices[0]}")
            
            return audio_int16, sample_rate
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            import traceback
            traceback.print_exc()
            raise

    @modal.asgi_app()
    def web(self):
        """FastAPI ASGI app for Kokoro TTS"""
        from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        import json

        web_app = FastAPI(title="Kokoro TTS Service")

        web_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        class TTSRequest(BaseModel):
            text: str
            voice: str = None

        # Store reference to self for use in endpoints
        instance = self

        @web_app.get("/status")
        async def status():
            """Health check endpoint"""
            try:
                return {
                    "status": "ok" if instance.tts_pipeline is not None else "initializing",
                    "model": "kokoro-82m",
                    "sample_rate": instance.sample_rate,
                    "available_voices": instance.available_voices,
                    "device": instance.device,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}, 500

        @web_app.get("/voices")
        async def get_voices():
            """Get list of all available voices"""
            try:
                return {
                    "voices": instance.available_voices,
                    "count": len(instance.available_voices),
                }
            except Exception as e:
                return {"error": str(e)}, 500

        @web_app.post("/tts")
        async def tts_endpoint(request: TTSRequest):
            """HTTP endpoint for TTS"""
            try:
                if not request.text:
                    return {"error": "No text provided"}, 400
                
                if instance.tts_pipeline is None:
                    return {"error": "Service not initialized"}, 503
                
                audio, sample_rate = instance.generate_audio(request.text, request.voice)
                # Convert to bytes
                audio_bytes = audio.tobytes()
                return Response(
                    content=audio_bytes,
                    media_type="audio/wav",
                    headers={
                        "X-Sample-Rate": str(sample_rate),
                        "X-Audio-Length": str(len(audio_bytes)),
                        "X-Voice": request.voice or instance.available_voices[0],
                    }
                )
            except Exception as e:
                print(f"TTS endpoint error: {e}")
                import traceback
                traceback.print_exc()
                return {"error": str(e)}, 500

        @web_app.websocket("/ws")
        async def websocket(ws: WebSocket):
            """WebSocket endpoint for streaming TTS"""
            await ws.accept()
            print("Kokoro TTS WebSocket connection established")

            try:
                while True:
                    # Receive text message
                    try:
                        data = await ws.receive_text()
                    except Exception as e:
                        print(f"Error receiving message: {e}")
                        break
                    
                    if not data or len(data.strip()) == 0:
                        continue
                    
                    print(f"Received text for TTS: {data[:50]}...")
                    
                    try:
                        # Parse request (can be JSON or plain text)
                        try:
                            request_data = json.loads(data)
                            text = request_data.get("text", "")
                            voice = request_data.get("voice", None)
                        except json.JSONDecodeError:
                            # Plain text
                            text = data
                            voice = None
                        
                        if not text or len(text.strip()) == 0:
                            continue
                        
                        if instance.tts_pipeline is None:
                            error_msg = b"\x03" + "Service not initialized".encode('utf-8')
                            await ws.send_bytes(error_msg)
                            continue
                        
                        # Generate audio
                        audio, sample_rate = instance.generate_audio(text, voice)
                        
                        # Send audio data
                        # Format: [tag: 1 byte][sample_rate: 4 bytes][voice_len: 2 bytes][voice][audio_data: bytes]
                        audio_bytes = audio.tobytes()
                        sr_bytes = sample_rate.to_bytes(4, byteorder='big')
                        used_voice = voice or instance.available_voices[0]
                        voice_bytes = used_voice.encode('utf-8')
                        voice_len = len(voice_bytes).to_bytes(2, byteorder='big')
                        msg = b"\x01" + sr_bytes + voice_len + voice_bytes + audio_bytes
                        await ws.send_bytes(msg)
                        
                        print(f"Sent audio: {len(audio_bytes)} bytes, sample rate: {sample_rate}, voice: {used_voice}")
                        
                    except Exception as e:
                        print(f"Error generating TTS: {e}")
                        import traceback
                        traceback.print_exc()
                        error_msg = b"\x03" + str(e).encode('utf-8')
                        try:
                            await ws.send_bytes(error_msg)
                        except:
                            pass

            except WebSocketDisconnect:
                print("WebSocket disconnected")
            except Exception as e:
                print(f"WebSocket exception: {e}")
                import traceback
                traceback.print_exc()
            finally:
                try:
                    await ws.close(code=1000)
                except:
                    pass

        return web_app
