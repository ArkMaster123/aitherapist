# Groq Ultra-Fast Agent Setup

## Setup Groq API Key

1. **Create Modal secret**:
   ```bash
   modal secret create groq-api GROQ_API_KEY=your-groq-api-key
   ```

2. **Or set in environment** (for local testing):
   ```bash
   export GROQ_API_KEY=your-groq-api-key
   ```

## Optional: Cartesia TTS (40ms - fastest!)

If you want the fastest TTS (40ms vs 97ms):

1. **Get Cartesia API key** from https://cartesia.ai
2. **Create Modal secret**:
   ```bash
   modal secret create cartesia-api CARTESIA_API_KEY=your-cartesia-key
   ```

3. **Or it will fallback to Kokoro-82m** (97ms, still very fast!)

## Deploy

```bash
cd modal-backend
modal deploy -m src.groq_ultra_fast_agent
```

## Performance

- **STT**: Groq Whisper Large v3 Turbo (216x real-time, ~631ms for 5-sec audio)
- **LLM**: Qwen2.5-7B via vLLM (300-500ms streaming)
- **TTS**: Cartesia (40ms) or Kokoro (97ms)
- **Effective latency**: ~340-540ms (faster than ElevenLabs!)

## Why This is Better

1. **Groq is 10-50x faster** than Faster-Whisper
2. **No GPU needed for STT** (API-based, saves GPU for TTS)
3. **Processes while user speaks** (effective latency is lower)
4. **You already have the API key!** ✅
