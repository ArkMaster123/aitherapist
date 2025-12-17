# VibeVoice-Realtime-0.5B TTS Backend

Ultra-fast text-to-speech using Microsoft's VibeVoice-Realtime-0.5B model.

## Features

- **Ultra-low latency**: ~300ms first-word latency
- **Real-time streaming**: Supports streaming TTS generation
- **Lightweight**: Only 0.5B parameters
- **High quality**: Natural-sounding speech synthesis

## Setup

### 1. Deploy to Modal

```bash
cd modal-backend
modal deploy -m src.vibevoice_tts
```

### 2. Get WebSocket URL

The deployment will give you a URL like:
```
wss://your-username--therapist-voice-chat-vibevoice-tts-web.modal.run/ws
```

### 3. Set Environment Variables

Add to your `.env.local`:
```
MODAL_USERNAME=your-modal-username
MODAL_APP_NAME=therapist-voice-chat
```

## Usage

### WebSocket API

Connect to `/ws` endpoint and send text messages:

```javascript
const ws = new WebSocket('wss://your-url/ws');

// Send plain text
ws.send('Hello, this is a test');

// Or send JSON with options
ws.send(JSON.stringify({
  text: 'Hello, this is a test',
  speaker: 'Emma',  // Optional: Emma, Mike, Grace, etc.
  cfg_scale: 1.5,    // Optional: quality vs speed (1.0-2.0)
  ddpm_steps: 5      // Optional: generation steps (3-10)
}));

// Receive audio
ws.onmessage = (event) => {
  const data = event.data;
  if (data instanceof ArrayBuffer) {
    const view = new Uint8Array(data);
    const tag = view[0];
    
    if (tag === 0x01) {
      // Audio data: [tag][sample_rate: 4 bytes][audio: int16 bytes]
      const sr = new DataView(data, 1, 4).getUint32(0, false);
      const audioBytes = data.slice(5);
      // Process audio...
    } else if (tag === 0x03) {
      // Error message
      const error = new TextDecoder().decode(data.slice(1));
      console.error('TTS Error:', error);
    }
  }
};
```

### HTTP API

POST to `/tts` endpoint:

```bash
curl -X POST https://your-url/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test"}' \
  --output output.wav
```

## Integration with Voice2 Page

The voice2 page can use this TTS backend to convert LLM text responses to speech in real-time.

## Performance

- **First-word latency**: ~300ms
- **Real-time factor**: < 0.1 (10x faster than real-time)
- **GPU**: A10G (scales to 0 when idle)

## Available Speakers

Default speakers available:
- Emma (English, female)
- Mike (English, male)
- Grace (English, female)
- Carter, Davis, Frank, Samuel (various accents)

## Notes

- Model requires GPU for optimal performance
- First request may be slower due to model warmup
- Supports streaming for lower latency
- Audio format: 24kHz, 16-bit PCM
