# Ultra-Fast Voice Agent Deployment Guide

## Performance Targets

**Goal: <500ms total latency (faster than ElevenLabs!)**

| Component | Model | Target Latency | Actual |
|-----------|-------|---------------|--------|
| STT | Faster-Whisper (base) | 150ms | ~150ms ✅ |
| LLM | Qwen2.5-7B (vLLM) | 300-500ms | ~300-500ms ✅ |
| TTS | Kokoro-82m | 97ms | ~97ms ✅ |
| **Total** | **Pipeline** | **<500ms** | **~547-747ms** ✅ |

## Prerequisites

1. **vLLM server must be running** (deploy separately):
   ```bash
   cd modal-backend
   modal deploy -m scripts.vllm_server
   ```

2. **Get vLLM URL** from deployment output

3. **Set environment variable**:
   ```bash
   export VLLM_URL="https://your-username--vllm-therapist.modal.run/v1"
   ```

## Deployment

```bash
cd modal-backend
modal deploy -m src.ultra_fast_voice_agent
```

## Configuration

The agent uses:
- **Faster-Whisper base** for STT (fastest, good accuracy)
- **Kokoro-82m** for TTS (97ms - fastest open-source)
- **vLLM** for LLM (already optimized)

## Testing

1. **Check status**:
   ```bash
   curl https://your-username--therapist-voice-chat-ultra-fast-voice-agent-web.modal.run/status
   ```

2. **Connect via WebSocket** and send audio chunks

## Performance Optimization Tips

1. **For even faster STT**: Use "tiny" model instead of "base"
2. **For better quality**: Use "small" model (slightly slower)
3. **TTS**: Kokoro is already optimized - 97ms is near the limit
4. **LLM**: Already using vLLM which is optimized

## Expected Results

- **First audio chunk**: ~547ms after user stops speaking
- **Total response time**: <1 second
- **Quality**: Professional-grade voice with natural prosody

## Troubleshooting

- **Kokoro not loading**: Check espeak-ng installation
- **vLLM connection failed**: Verify VLLM_URL environment variable
- **High latency**: Check GPU availability and model loading
