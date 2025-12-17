"""
VibeVoice-Realtime-0.5B TTS websocket server for ultra-fast text-to-speech.
Based on Microsoft's VibeVoice-Realtime-0.5B model.
"""

import modal
import time
import numpy as np
import os

from .common import app

model_path = "/models"
model_volume_cache = modal.Volume.from_name("vibevoice-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .run_commands(
        "git clone https://github.com/vibevoice-community/VibeVoice.git /tmp/VibeVoice",
        "cd /tmp/VibeVoice && pip install -e .",
    )
    .pip_install(
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
        "transformers>=4.30.0",
        "soundfile",
        "numpy",
        "scipy",
        "fastapi==0.115.5",
        "huggingface_hub==0.24.7",
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
    import torchaudio
    from huggingface_hub import snapshot_download
    import sys
    # Add VibeVoice to path
    if os.path.exists("/tmp/VibeVoice"):
        sys.path.insert(0, "/tmp/VibeVoice")


@app.cls(
    image=image,
    gpu="A100",
    scaledown_window=3600,  # 1 hour = 3600 seconds (max allowed by Modal)
    timeout=600,
    volumes={model_path: model_volume_cache},
)
class VibeVoiceTTS:
    @modal.enter()
    def enter(self):
        """Initialize the VibeVoice-Realtime TTS model on container startup"""
        try:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Loading VibeVoice-Realtime-0.5B on {self.device}...")
            
            # Try to import VibeVoice from the cloned repo
            use_vibevoice_package = False
            try:
                from vibevoice import VibeVoice
                use_vibevoice_package = True
                print("Using VibeVoice package")
            except ImportError:
                print("VibeVoice package not found, using transformers fallback")
                use_vibevoice_package = False
            
            # Download model
            model_id = "microsoft/VibeVoice-Realtime-0.5B"
            print(f"Downloading model {model_id}...")
            model_dir = snapshot_download(
                repo_id=model_id,
                cache_dir=model_path,
                local_files_only=False
            )
            print(f"Model downloaded to {model_dir}")
            
            if use_vibevoice_package:
                # Use VibeVoice package if available
                from vibevoice import VibeVoice
                self.model = VibeVoice.from_pretrained(
                    model_path=model_dir,
                    device=self.device
                )
                self.processor = None
                self.use_vibevoice_package = True
            else:
                # Fallback: use transformers directly
                from transformers import AutoProcessor, AutoModel
                self.processor = AutoProcessor.from_pretrained(model_id, cache_dir=model_path)
                self.model = AutoModel.from_pretrained(model_id, cache_dir=model_path)
                self.model.to(self.device)
                self.model.eval()
                self.use_vibevoice_package = False
            
            # Default speaker (can be changed via API)
            self.default_speaker = "Emma"
            self.sample_rate = 24000  # VibeVoice standard sample rate
            
            print(f"✅ VibeVoice-Realtime-0.5B loaded successfully. Sample rate: {self.sample_rate}")
            
            # Verify the model works with a test generation
            try:
                test_audio, _ = self._generate_audio_internal("test", self.default_speaker, 1.5, 5)
                print(f"✅ Test generation successful: {len(test_audio)} samples")
            except Exception as e:
                print(f"⚠️ Test generation failed: {e}. Service may have issues.")
                
        except Exception as e:
            print(f"❌ CRITICAL: Failed to initialize VibeVoice TTS: {e}")
            import traceback
            traceback.print_exc()
            # Set safe defaults so the service can at least start
            self.device = "cpu"
            self.model = None
            self.processor = None
            self.use_vibevoice_package = False
            self.default_speaker = "Emma"
            self.sample_rate = 24000
            raise  # Re-raise to fail fast during initialization

    def _generate_audio_internal(self, text: str, speaker: str = None, cfg_scale: float = 1.5, ddpm_steps: int = 5):
        """Internal method to generate audio - called by public method"""
        if self.model is None:
            raise RuntimeError("VibeVoice model not initialized")
            
        speaker = speaker or self.default_speaker
        
        with torch.no_grad():
            if self.use_vibevoice_package:
                # Use VibeVoice package method
                audio = self.model.generate(
                    text=text,
                    speaker_name=speaker,
                    cfg_scale=cfg_scale,
                    ddpm_steps=ddpm_steps,
                )
            else:
                # Fallback: use transformers generate
                inputs = self.processor(text=text, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                outputs = self.model.generate(**inputs)
                
                # Extract audio from outputs
                if hasattr(outputs, 'audio_values'):
                    audio = outputs.audio_values
                elif isinstance(outputs, torch.Tensor):
                    audio = outputs
                elif isinstance(outputs, (list, tuple)) and len(outputs) > 0:
                    audio = outputs[0]
                else:
                    raise ValueError("Could not extract audio from model output")
            
            # Convert to numpy array
            if isinstance(audio, torch.Tensor):
                audio = audio.cpu().numpy()
            
            # Ensure audio is 1D
            if len(audio.shape) > 1:
                audio = audio.flatten()
            
            # Normalize audio to int16
            max_val = np.max(np.abs(audio)) if len(audio) > 0 else 1.0
            if max_val > 1.0 and max_val > 0:
                audio = audio / max_val
            audio_int16 = (audio * 32767).astype(np.int16)
            
            return audio_int16, self.sample_rate

    def generate_audio(self, text: str, speaker: str = None, cfg_scale: float = 1.5, ddpm_steps: int = 5):
        """Generate audio from text using VibeVoice"""
        try:
            start_time = time.time()
            
            if not text or len(text.strip()) == 0:
                raise ValueError("Text cannot be empty")
            
            audio_int16, sample_rate = self._generate_audio_internal(text, speaker, cfg_scale, ddpm_steps)
            
            latency = (time.time() - start_time) * 1000
            print(f"🎯 VibeVoice TTS latency: {latency:.1f}ms, speaker: {speaker or self.default_speaker}")
            
            return audio_int16, sample_rate
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            import traceback
            traceback.print_exc()
            raise

    @modal.asgi_app()
    def web(self):
        """FastAPI ASGI app for VibeVoice TTS"""
        from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
        from fastapi.middleware.cors import CORSMiddleware
        import json

        web_app = FastAPI(title="VibeVoice-Realtime TTS Service")

        web_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Store reference to self for use in endpoints
        instance = self

        @web_app.get("/status")
        async def status():
            """Health check endpoint"""
            try:
                return {
                    "status": "ok" if instance.model is not None else "initializing",
                    "model": "vibevoice-realtime-0.5b",
                    "sample_rate": instance.sample_rate,
                    "default_speaker": instance.default_speaker,
                    "device": instance.device,
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}, 500

        @web_app.post("/tts")
        async def tts_endpoint(request: dict):
            """HTTP endpoint for TTS"""
            try:
                text = request.get("text", "")
                if not text:
                    return {"error": "No text provided"}, 400
                
                if instance.model is None:
                    return {"error": "Service not initialized"}, 503
                
                speaker = request.get("speaker", instance.default_speaker)
                cfg_scale = request.get("cfg_scale", 1.5)
                ddpm_steps = request.get("ddpm_steps", 5)
                
                audio, sample_rate = instance.generate_audio(text, speaker, cfg_scale, ddpm_steps)
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
            print("VibeVoice TTS WebSocket connection established")

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
                            speaker = request_data.get("speaker", instance.default_speaker)
                            cfg_scale = request_data.get("cfg_scale", 1.5)
                            ddpm_steps = request_data.get("ddpm_steps", 5)
                        except json.JSONDecodeError:
                            # Plain text
                            text = data
                            speaker = instance.default_speaker
                            cfg_scale = 1.5
                            ddpm_steps = 5
                        
                        if not text or len(text.strip()) == 0:
                            continue
                        
                        if instance.model is None:
                            error_msg = b"\x03" + "Service not initialized".encode('utf-8')
                            await ws.send_bytes(error_msg)
                            continue
                        
                        # Generate audio
                        audio, sample_rate = instance.generate_audio(text, speaker, cfg_scale, ddpm_steps)
                        
                        # Send audio data
                        # Format: [tag: 1 byte][sample_rate: 4 bytes][audio_data: bytes]
                        audio_bytes = audio.tobytes()
                        sr_bytes = sample_rate.to_bytes(4, byteorder='big')
                        msg = b"\x01" + sr_bytes + audio_bytes
                        await ws.send_bytes(msg)
                        
                        print(f"Sent audio: {len(audio_bytes)} bytes, sample rate: {sample_rate}, speaker: {speaker}")
                        
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
