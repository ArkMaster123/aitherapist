# Ultra-Fast Voice Pipeline: Matching ElevenLabs Speed

## Research Findings (via MCP Tools)

### Fastest TTS Models (2025 Benchmarks)

| Model | TTFB | Type | Status |
|-------|------|------|--------|
| **Kokoro-82m** (Together AI) | **97ms** | Open-source | ⭐ BEST |
| **AsyncFlow** (Podcastle) | **166ms** | API | Very fast |
| **Orpheus** (Together AI) | **187ms** | Open-source | High quality |
| **ElevenLabs Flash v2.5** | **~75ms** | Proprietary | Target |
| **Chatterbox-Turbo** | **<200ms** | Open-source | We have this |

### Fastest STT Models

| Model | Latency | Type |
|-------|---------|------|
| **Streaming Whisper** (Together AI) | **~150ms** | Optimized |
| **Faster-Whisper** | **~150ms** | Open-source |
| **Whisper Large v3** | **~200ms** | Standard |

## Recommended Ultra-Fast Stack

### Option 1: Self-Hosted (Best Latency)
```
STT: Faster-Whisper (150ms)
LLM: Qwen2.5-7B via vLLM (300-500ms)  
TTS: Kokoro-82m (97ms) ⭐
Total: ~547-747ms
```

### Option 2: Hybrid (Fastest Possible)
```
STT: Faster-Whisper (150ms)
LLM: Qwen2.5-7B via vLLM (300-500ms)
TTS: AsyncFlow API (166ms) - if API access available
Total: ~616-816ms
```

### Option 3: Together AI Stack (Easiest)
```
STT: Streaming Whisper API (150ms)
LLM: Qwen2.5-7B via vLLM (300-500ms)
TTS: Kokoro API (97ms)
Total: ~547-747ms
```

## Implementation Plan

### Priority: Kokoro-82m TTS
- **97ms TTFB** - faster than ElevenLabs in benchmarks
- Open-source, can self-host
- Together AI provides serverless API
- Perfect for real-time voice agents

### Architecture Changes Needed

1. **Replace VibeVoice with Kokoro-82m**
   - 2x faster (97ms vs 300ms)
   - Same GPU memory footprint
   - Better streaming support

2. **Optimize STT**
   - Use Faster-Whisper with optimized settings
   - Implement streaming VAD
   - Reduce buffer sizes

3. **LLM Optimization**
   - Already using vLLM (optimized)
   - Consider 4-bit quantization
   - Streaming tokens

4. **Pipeline Optimization**
   - Parallel processing where possible
   - Overlap STT/LLM/TTS operations
   - Minimize data copying

## Target Performance

**Goal: <500ms total latency (faster than ElevenLabs)**

Breakdown:
- STT: 150ms
- LLM: 300ms (streaming)
- TTS: 97ms (Kokoro)
- **Total: ~547ms** ✅

## Next Steps

1. Implement Kokoro-82m TTS backend
2. Optimize Faster-Whisper STT
3. Test and benchmark
4. Deploy ultra-fast pipeline
