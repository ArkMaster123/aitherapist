# Ultra-Fast Voice Agent Setup
## Target: Sub-200ms Latency (Matching ElevenLabs Performance)

### Performance Comparison

| Component | Model | Latency | Notes |
|-----------|-------|---------|-------|
| **STT** | Faster-Whisper (base) | ~150ms | Fast, accurate |
| **LLM** | Qwen2.5-7B (vLLM) | ~300-500ms | Streaming tokens |
| **TTS** | **VoXtream (compiled)** | **~102ms** ⚡ | **FASTEST OPEN SOURCE** |
| **Total** | Integrated Pipeline | **~550-750ms** | With optimizations |

### Why VoXtream?

- ✅ **102ms latency** (compiled on A100) - closest to ElevenLabs' 75ms
- ✅ **Open source** (MIT/Apache 2.0)
- ✅ **Zero-shot voice cloning** (3-5 second sample)
- ✅ **Streaming support** (80ms chunks)
- ✅ **Only ~2GB VRAM** required
- ✅ **5x faster than real-time**

### Installation

```bash
cd modal-backend
modal deploy -m src.ultra_fast_voice_agent
```

### Requirements

1. **vLLM server running** (separate deployment):
   ```bash
   modal deploy -m scripts.vllm_server
   ```

2. **Environment variables**:
   ```
   MODAL_USERNAME=your-modal-username
   MODAL_APP_NAME=therapist-voice-chat
   ```

### Usage

Connect to WebSocket with vLLM URL:
```
wss://your-username--therapist-voice-chat-ultra-fast-voice-agent-web.modal.run/ws?vllm_url=https://your-vllm-url
```

### Protocol

**Send**: Opus-encoded audio chunks (16kHz, 16-bit PCM)

**Receive**:
- `\x01` + [sample_rate: 4 bytes] + [audio: int16 bytes] - TTS audio
- `\x02` + [text: utf-8 bytes] - STT transcript
- `\x03` + [error: utf-8 bytes] - Error message

### Performance Tips

1. **VoXtream Compilation**: Model compiles on first use (~30s), then runs at 102ms
2. **STT Buffering**: Processes in 500ms chunks for better accuracy
3. **LLM Streaming**: Tokens stream as they generate
4. **TTS Streaming**: Audio chunks generated in 80ms intervals

### Benchmark Results

From VoXtream paper:
- **A100 (compiled)**: 102ms FPL, 0.17 RTF
- **RTX3090 (compiled)**: 123ms FPL, 0.19 RTF

### Comparison with ElevenLabs

| Metric | ElevenLabs Flash | VoXtream (Compiled) |
|--------|------------------|---------------------|
| **Latency** | ~75ms | ~102ms |
| **Cost** | Pay per character | Free (self-hosted) |
| **Voice Cloning** | Yes | Yes (zero-shot) |
| **Open Source** | ❌ | ✅ |
| **Streaming** | Yes | Yes |

### Next Steps

1. Deploy ultra-fast voice agent
2. Test latency with real conversations
3. Optimize further if needed (model quantization, etc.)
4. Consider Rime Mist v2 API if you need sub-100ms (requires API key)
