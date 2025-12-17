# TTS Services on Modal

This document describes the three TTS (Text-to-Speech) services hosted on Modal:

1. **Kokoro TTS** - Fast open-source TTS with voice selection
2. **ResembleAI/Chatterbox-Turbo** - High-quality TTS with voice cloning
3. **VibeVoice-Realtime-0.5B** - Microsoft's realtime streaming TTS

All services are configured to automatically scale down after 24 hours of inactivity to save costs.

## Features

### Auto-Scale Down
All services use `scaledown_window=86400` (24 hours), meaning:
- Services stay warm for 24 hours after the last request
- After 24 hours of inactivity, the GPU scales down to 0
- Next request will have a cold start (~30-60 seconds) but saves costs

### Service Endpoints

#### 1. Kokoro TTS (`kokoro_tts.py`)

**Model**: Kokoro-82m  
**Sample Rate**: 24kHz  
**Latency**: ~97ms  
**Voices**: Multiple voices available via dropdown

**Deploy**:
```bash
modal deploy -m src.kokoro_tts
```

**Endpoints**:
- `GET /status` - Service status and available voices
- `GET /voices` - List all available voices
- `POST /tts` - HTTP TTS endpoint
  ```json
  {
    "text": "Hello, world!",
    "voice": "af_bella"  // optional, defaults to first voice
  }
  ```
- `WebSocket /ws` - Streaming TTS
  ```json
  {
    "text": "Hello, world!",
    "voice": "af_bella"  // optional
  }
  ```

**Available Voices** (examples):
- `af_bella`, `af_sarah`, `af_sky`, `af_angelica`, `af_ana`
- `am_adam`, `am_michael`, `am_sam`, `am_mitchell`, `am_douglas`
- `bf_donna`, `bf_emma`, `bf_emily`, `bf_olivia`, `bf_samantha`
- `bm_antonio`, `bm_anthony`, `bm_george`, `bm_james`, `bm_robert`

#### 2. Chatterbox-Turbo TTS (`chatterbox.py`)

**Model**: ResembleAI/Chatterbox-Turbo  
**Sample Rate**: Model-dependent  
**Features**: Voice cloning support

**Deploy**:
```bash
modal deploy -m src.chatterbox
```

**Endpoints**:
- `GET /status` - Service status and cloned voices
- `GET /voices` - List all cloned voices
- `POST /clone-voice` - Clone a voice from audio file
  ```
  Form data:
  - voice_id: string (unique identifier)
  - audio_file: file (WAV format recommended)
  ```
- `DELETE /voices/{voice_id}` - Delete a cloned voice
- `POST /tts` - HTTP TTS endpoint
  ```json
  {
    "text": "Hello, world!",
    "voice_id": "my_voice",  // optional, use cloned voice
    "audio_prompt_path": "/path/to/audio.wav"  // optional, direct path
  }
  ```
- `WebSocket /ws` - Streaming TTS
  - Query params: `voice_id` or `audio_prompt`
  - Message format: JSON or plain text
  ```json
  {
    "text": "Hello, world!",
    "voice_id": "my_voice"  // optional
  }
  ```

**Voice Cloning Workflow**:
1. Upload audio file via `POST /clone-voice` with a unique `voice_id`
2. Use the `voice_id` in subsequent TTS requests
3. The cloned voice is stored and can be reused

#### 3. VibeVoice-Realtime-0.5B (`vibevoice_tts.py`)

**Model**: Microsoft VibeVoice-Realtime-0.5B  
**Sample Rate**: 24kHz  
**Latency**: ~300ms first audible  
**Features**: Streaming text input, realtime TTS

**Deploy**:
```bash
modal deploy -m src.vibevoice_tts
```

**Endpoints**:
- `GET /status` - Service status
- `POST /tts` - HTTP TTS endpoint
  ```json
  {
    "text": "Hello, world!",
    "speaker": "Emma",  // optional
    "cfg_scale": 1.5,   // optional
    "ddpm_steps": 5     // optional
  }
  ```
- `WebSocket /ws` - Streaming TTS with realtime text input
  ```json
  {
    "text": "Hello, world!",
    "speaker": "Emma",      // optional
    "cfg_scale": 1.5,       // optional
    "ddpm_steps": 5         // optional
  }
  ```

**Features**:
- Supports streaming text input (can send text chunks as they arrive)
- Optimized for long-form speech generation
- Single speaker model (English only)

## Usage Examples

### Python Client Example

```python
import requests
import json

# Kokoro TTS
response = requests.post(
    "https://your-username--therapist-voice-chat-kokoro-tts-web.modal.run/tts",
    json={"text": "Hello, world!", "voice": "af_bella"}
)
audio_data = response.content

# Chatterbox TTS with voice cloning
# 1. Clone a voice
with open("voice_sample.wav", "rb") as f:
    response = requests.post(
        "https://your-username--chatterbox-tts-chatterbox-tts-web.modal.run/clone-voice",
        files={"audio_file": f},
        data={"voice_id": "my_voice"}
    )

# 2. Use cloned voice
response = requests.post(
    "https://your-username--chatterbox-tts-chatterbox-tts-web.modal.run/tts",
    json={"text": "Hello, world!", "voice_id": "my_voice"}
)
audio_data = response.content

# VibeVoice TTS
response = requests.post(
    "https://your-username--therapist-voice-chat-vibevoice-tts-web.modal.run/tts",
    json={"text": "Hello, world!", "speaker": "Emma"}
)
audio_data = response.content
```

### WebSocket Example (JavaScript)

```javascript
// Kokoro TTS WebSocket
const ws = new WebSocket('wss://your-username--therapist-voice-chat-kokoro-tts-web.modal.run/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    text: "Hello, world!",
    voice: "af_bella"
  }));
};

ws.onmessage = (event) => {
  if (event.data instanceof ArrayBuffer) {
    const data = new Uint8Array(event.data);
    const tag = data[0];
    
    if (tag === 0x01) {
      // Audio data
      const sampleRate = new DataView(data.buffer, 1, 4).getUint32(0, false);
      const audioData = data.slice(5);
      // Process audio...
    } else if (tag === 0x03) {
      // Error
      const error = new TextDecoder().decode(data.slice(1));
      console.error('Error:', error);
    }
  }
};
```

## Cost Optimization

All services are configured with:
- **24-hour scaledown**: Services automatically pause after 24 hours of inactivity
- **GPU**: A10G (cost-effective for TTS workloads)
- **Volume caching**: Models are cached in Modal volumes to speed up cold starts

**Cost Savings**:
- Without scaledown: ~$0.30-0.50/hour (always running)
- With 24-hour scaledown: Only pay when in use + cold start time

## Development

### Local Testing

```bash
# Test Kokoro TTS
modal serve -m src.kokoro_tts

# Test Chatterbox TTS
modal serve -m src.chatterbox

# Test VibeVoice TTS
modal serve -m src.vibevoice_tts
```

### Deployment

```bash
# Deploy all services
modal deploy -m src.kokoro_tts
modal deploy -m src.chatterbox
modal deploy -m src.vibevoice_tts
```

## Troubleshooting

### Cold Start Delays
- First request after 24 hours may take 30-60 seconds
- This is normal - Modal needs to load the model into GPU memory
- Subsequent requests are fast (~100-300ms)

### Voice Cloning Issues
- Ensure audio file is in WAV format
- Recommended: 16kHz mono, 3-10 seconds of clear speech
- Longer files may work but may increase latency

### Model Loading Errors
- Check Modal logs: `modal logs <app-name>`
- Ensure GPU quota is available
- Verify model downloads completed successfully

## Next Steps

1. Deploy all three services to Modal
2. Test each service with sample requests
3. Integrate into your application
4. Monitor costs and usage via Modal dashboard

