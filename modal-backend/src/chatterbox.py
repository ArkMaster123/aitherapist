"""
Chatterbox-Turbo TTS websocket server for text-to-speech.
Based on Resemble AI's Chatterbox-Turbo model.
"""

import modal
import time
import numpy as np

from .chatterbox_common import app

model_path = "/models"
model_volume_cache = modal.Volume.from_name("chatterbox-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(
        "chatterbox-tts==0.1.6",
        "fastapi[standard]==0.124.4",
        "peft==0.18.0",
        "torchaudio",
        "torch",
        "numpy",
        "scipy",
        "huggingface_hub",
        "hf_transfer==0.1.8",
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
    import torchaudio as ta
    from chatterbox.tts_turbo import ChatterboxTurboTTS


@app.cls(
    image=image,
    gpu="A100",
    scaledown_window=3600,  # 1 hour = 3600 seconds (max allowed by Modal)
    timeout=600,
    volumes={model_path: model_volume_cache},
    secrets=[modal.Secret.from_name("huggingface-secret")],  # Required for downloading Chatterbox model
)
class ChatterboxTTS:
    @modal.enter()
    def enter(self):
        """Initialize the Chatterbox-Turbo TTS model on container startup"""
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading Chatterbox-Turbo on {self.device}...")
            
            # Load the Turbo model (ChatterboxTurboTTS is imported in image.imports())
            self.model = ChatterboxTurboTTS.from_pretrained(device=self.device)
            self.sample_rate = self.model.sr
            
            # Store cloned voices (voice_id -> audio_prompt_path)
            self.cloned_voices = {}
            
            print(f"✅ Chatterbox-Turbo loaded successfully. Sample rate: {self.sample_rate}")
            
            # Verify the model works with a test generation
            try:
                test_audio, _ = self._generate_audio_internal("test", None, None)
                print(f"✅ Test generation successful: {len(test_audio)} samples")
            except Exception as e:
                print(f"⚠️ Test generation failed: {e}. Service may have issues.")
                
        except Exception as e:
            print(f"❌ CRITICAL: Failed to initialize Chatterbox-Turbo TTS: {e}")
            import traceback
            traceback.print_exc()
            # Set safe defaults so the service can at least start
            self.device = "cpu"
            self.model = None
            self.sample_rate = 24000
            self.cloned_voices = {}
            raise  # Re-raise to fail fast during initialization

    def _generate_audio_internal(self, text: str, audio_prompt_path: str = None, voice_id: str = None):
        """Internal method to generate audio - called by public method"""
        if self.model is None:
            raise RuntimeError("Chatterbox model not initialized")
            
        # Check if using a cloned voice
        if voice_id and voice_id in self.cloned_voices:
            audio_prompt_path = self.cloned_voices[voice_id]
        
        # Generate audio
        with torch.no_grad():
            if audio_prompt_path:
                wav = self.model.generate(text, audio_prompt_path=audio_prompt_path)
            else:
                wav = self.model.generate(text)
        
        # Convert to numpy array if needed
        if isinstance(wav, torch.Tensor):
            wav = wav.cpu().numpy()
        
        # Ensure it's a 1D array
        if len(wav.shape) > 1:
            wav = wav.flatten()
        
        # Normalize audio to int16 range
        max_val = np.max(np.abs(wav)) if len(wav) > 0 else 1.0
        if max_val > 1.0 and max_val > 0:
            wav = wav / max_val
        wav_int16 = (wav * 32767).astype(np.int16)
        
        return wav_int16, self.sample_rate

    def generate_audio(self, text: str, audio_prompt_path: str = None, voice_id: str = None):
        """Generate audio from text using Chatterbox-Turbo with optional voice cloning"""
        try:
            start_time = time.time()
            
            if not text or len(text.strip()) == 0:
                raise ValueError("Text cannot be empty")
            
            audio_int16, sample_rate = self._generate_audio_internal(text, audio_prompt_path, voice_id)
            
            latency = (time.time() - start_time) * 1000
            print(f"🎯 Chatterbox TTS latency: {latency:.1f}ms")
            
            return audio_int16, sample_rate
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            import traceback
            traceback.print_exc()
            raise

    @modal.asgi_app()
    def web(self):
        """FastAPI ASGI app for Chatterbox-Turbo TTS"""
        from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect, File, UploadFile, Form
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        import tempfile
        import os
        import json

        web_app = FastAPI(title="Chatterbox-Turbo TTS Service")

        web_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        class TTSRequest(BaseModel):
            text: str
            voice_id: str = None
            audio_prompt_path: str = None

        # Store reference to self for use in endpoints
        instance = self

        @web_app.get("/status")
        async def status():
            """Health check endpoint"""
            try:
                return {
                    "status": "ok" if instance.model is not None else "initializing",
                    "model": "chatterbox-turbo",
                    "sample_rate": instance.sample_rate,
                    "cloned_voices": list(instance.cloned_voices.keys()),
                    "device": instance.device,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}, 500

        @web_app.post("/clone-voice")
        async def clone_voice(
            voice_id: str = Form(...),
            audio_file: UploadFile = File(...)
        ):
            """Clone a voice from an audio file"""
            try:
                if instance.model is None:
                    return {"error": "Service not initialized"}, 503
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    content = await audio_file.read()
                    tmp_file.write(content)
                    tmp_path = tmp_file.name
                
                # Store the voice clone
                instance.cloned_voices[voice_id] = tmp_path
                
                return {
                    "status": "success",
                    "voice_id": voice_id,
                    "message": f"Voice '{voice_id}' cloned successfully",
                }
            except Exception as e:
                print(f"Error cloning voice: {e}")
                import traceback
                traceback.print_exc()
                return {"error": str(e)}, 500

        @web_app.get("/voices")
        async def get_voices():
            """Get list of all cloned voices"""
            try:
                return {
                    "cloned_voices": list(instance.cloned_voices.keys()),
                    "count": len(instance.cloned_voices),
                }
            except Exception as e:
                return {"error": str(e)}, 500

        @web_app.delete("/voices/{voice_id}")
        async def delete_voice(voice_id: str):
            """Delete a cloned voice"""
            try:
                if voice_id in instance.cloned_voices:
                    # Clean up the file
                    try:
                        if os.path.exists(instance.cloned_voices[voice_id]):
                            os.unlink(instance.cloned_voices[voice_id])
                    except Exception as e:
                        print(f"Error deleting voice file: {e}")
                    del instance.cloned_voices[voice_id]
                    return {"status": "success", "message": f"Voice '{voice_id}' deleted"}
                return {"error": "Voice not found"}, 404
            except Exception as e:
                return {"error": str(e)}, 500

        @web_app.post("/tts")
        async def tts_endpoint(request: TTSRequest):
            """HTTP endpoint for TTS"""
            try:
                if not request.text:
                    return {"error": "No text provided"}, 400
                
                if instance.model is None:
                    return {"error": "Service not initialized"}, 503
                
                audio, sample_rate = instance.generate_audio(
                    request.text,
                    request.audio_prompt_path,
                    request.voice_id
                )
                # Convert to bytes
                audio_bytes = audio.tobytes()
                return Response(
                    content=audio_bytes,
                    media_type="audio/wav",
                    headers={
                        "X-Sample-Rate": str(sample_rate),
                        "X-Audio-Length": str(len(audio_bytes)),
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
            print("Chatterbox TTS WebSocket connection established")

            # Get audio prompt path or voice_id from query params (optional)
            audio_prompt_path = ws.query_params.get("audio_prompt", None)
            voice_id = ws.query_params.get("voice_id", None)

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
                            request_voice_id = request_data.get("voice_id", voice_id)
                            request_audio_prompt = request_data.get("audio_prompt_path", audio_prompt_path)
                        except json.JSONDecodeError:
                            # Plain text
                            text = data
                            request_voice_id = voice_id
                            request_audio_prompt = audio_prompt_path
                        
                        if not text or len(text.strip()) == 0:
                            continue
                        
                        if instance.model is None:
                            error_msg = b"\x03" + "Service not initialized".encode('utf-8')
                            await ws.send_bytes(error_msg)
                            continue
                        
                        # Generate audio
                        audio, sample_rate = instance.generate_audio(
                            text,
                            request_audio_prompt,
                            request_voice_id
                        )
                        
                        # Send audio data
                        # Format: [tag: 1 byte][sample_rate: 4 bytes][audio_data: bytes]
                        audio_bytes = audio.tobytes()
                        sr_bytes = sample_rate.to_bytes(4, byteorder='big')
                        msg = b"\x01" + sr_bytes + audio_bytes
                        await ws.send_bytes(msg)
                        
                        print(f"Sent audio: {len(audio_bytes)} bytes, sample rate: {sample_rate}")
                        
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
