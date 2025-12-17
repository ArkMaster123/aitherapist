# Voice Agent Architecture

## Component Separation

### External Services (Not in Modal)
- **Groq Whisper API**: STT service (external HTTP API)
- **Cartesia API** (optional): TTS service (external HTTP API)

### Modal App Components
- **TTS**: Kokoro-82m (self-hosted, runs in Modal)
- **LLM**: Qwen2.5-7B via vLLM (runs in separate Modal app)
- **Orchestration**: WebSocket server, audio processing, pipeline coordination

## Data Flow

```
Client → Modal App (WebSocket)
  ↓
1. Receive audio chunks
  ↓
2. Call Groq API (external) → STT
  ↓
3. Call vLLM (separate Modal app) → LLM
  ↓
4. Generate TTS in Modal → Audio
  ↓
5. Send audio back to client
```

## Why This Architecture?

1. **Groq is external**: No need to run it in Modal, just call their API
2. **Saves GPU**: Only TTS needs GPU, STT is handled by Groq's infrastructure
3. **Faster**: Groq's optimized infrastructure is faster than self-hosting
4. **Cost-effective**: Pay per use for Groq, GPU only for TTS

## Setup

1. **Groq API Key**: Set in Modal secrets (external service)
2. **vLLM URL**: Point to your vLLM Modal deployment
3. **TTS**: Runs in Modal (Kokoro-82m) or use Cartesia API
