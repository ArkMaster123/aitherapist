# AI Therapist Voice Chat - Modal Backend

This is the Modal backend for the AI Therapist voice chat feature, powered by Kyutai's Moshi speech-to-speech model.

## Setup

### 1. Install Modal

```bash
pip install modal
```

### 2. Authenticate with Modal

```bash
modal setup
modal token new
```

### 3. Development Server

Run the Moshi websocket server in development mode:

```bash
modal serve -m src.moshi
```

This will output a URL like `https://your-username--therapist-voice-chat-moshi-web-dev.modal.run`

### 4. Deploy to Production

```bash
modal deploy -m src.moshi
```

This deploys the app and gives you a production URL.

## Architecture

- **Moshi Model**: Kyutai's speech-to-speech language model
- **MIMI Codec**: Neural audio codec for encoding/decoding
- **Opus Streaming**: Real-time audio compression over WebSocket
- **GPU**: A10G (scales to 0 when not in use)

## WebSocket Protocol

- Connect to `/ws` endpoint
- Send: Opus-encoded audio frames
- Receive: 
  - `\x01` prefix: Audio data (Opus)
  - `\x02` prefix: Text transcript

## Cost

Modal is serverless - you only pay for GPU time when users are connected.
The `scaledown_window=300` means GPUs stay warm for 5 minutes after the last user disconnects.
