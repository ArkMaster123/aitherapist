# Integrated Voice Agent Pipeline Plan
## STT → LLM → TTS in Single Modal App

### Pipeline Overview

```
User Speech → STT → LLM → TTS → Audio Output
   ↓           ↓      ↓      ↓
  Opus      Text   Text   Audio
  Audio    Tokens Response Stream
```

### Architecture Decision

**Current State:**
- Moshi: Speech-to-speech (all-in-one, but less control)
- Separate TTS backend: Higher latency due to network hops

**Proposed Solution:**
- **Single Modal App** with integrated STT, LLM, and TTS
- **Streaming at each stage** for minimal latency
- **Shared GPU memory** for all models
- **In-process communication** (no network overhead)

### Component Selection

#### 1. STT (Speech-to-Text)
**Options:**
- **Whisper (OpenAI)**: High accuracy, ~200ms latency
- **Faster-Whisper**: Optimized version, ~150ms latency ⭐ **RECOMMENDED**
- **WhisperX**: With word-level timestamps
- **Deepgram**: API-based, very fast but external dependency

**Choice: Faster-Whisper**
- Open source
- ~150ms latency
- Good accuracy
- Can run on same GPU as other models

#### 2. LLM (Language Model)
**Options:**
- **Qwen2.5-7B-Instruct** (already fine-tuned): ~300-500ms ⭐ **RECOMMENDED**
- **Llama 3.2-3B**: Faster but less capable
- **GPT-4o-mini**: API-based, adds network latency
- **vLLM server**: Already set up in codebase

**Choice: Qwen2.5-7B-Instruct (via vLLM)**
- Already fine-tuned for therapist conversations
- Streaming support
- Can run on same GPU with quantization
- ~300-500ms for response generation

#### 3. TTS (Text-to-Speech)
**Options:**
- **VibeVoice-Realtime-0.5B**: ~300ms, lightweight ⭐ **RECOMMENDED**
- **Chatterbox-Turbo**: Higher quality but slower
- **Coqui TTS**: Good quality, moderate speed
- **ElevenLabs**: API-based, very fast but external

**Choice: VibeVoice-Realtime-0.5B**
- ~300ms first-word latency
- Lightweight (0.5B parameters)
- Can share GPU with other models
- Streaming support

### Latency Targets

| Component | Target | Actual (Expected) |
|-----------|--------|-------------------|
| STT | <200ms | ~150ms (Faster-Whisper) |
| LLM | <500ms | ~300-500ms (Qwen2.5-7B) |
| TTS | <300ms | ~300ms (VibeVoice) |
| **Total** | **<1000ms** | **~750-950ms** |

### Implementation Architecture

```python
@app.cls(
    image=image,
    gpu="A10G",  # Shared GPU for all models
    scaledown_window=300,
    timeout=600,
)
class IntegratedVoiceAgent:
    @modal.enter()
    def enter(self):
        # Load all models on same GPU
        self.stt_model = load_faster_whisper()      # STT
        self.llm_client = connect_to_vllm()          # LLM (or load directly)
        self.tts_model = load_vibevoice()           # TTS
        
    @modal.asgi_app()
    def web(self):
        # Single WebSocket endpoint
        # Processes: Audio → Text → Response → Audio
```

### Data Flow

```
1. Receive Opus audio chunks from client
2. Decode Opus → PCM audio
3. STT: PCM → Text (streaming, partial results)
4. LLM: Text → Response (streaming tokens)
5. TTS: Response tokens → Audio (streaming)
6. Encode Audio → Opus
7. Send Opus chunks to client
```

### Streaming Strategy

**Parallel Processing:**
- STT processes audio chunks as they arrive
- LLM starts generating as soon as first sentence is complete
- TTS starts synthesizing as LLM tokens stream in
- **Overlap operations** to minimize total latency

**Example Timeline:**
```
t=0ms:   User starts speaking
t=150ms: STT outputs first words
t=200ms: LLM starts generating (STT still running)
t=500ms: LLM outputs first tokens
t=550ms: TTS starts synthesizing (LLM still generating)
t=850ms: First audio chunk ready
t=1000ms: Full response complete
```

### Memory Optimization

**Shared GPU Memory:**
- All models on same A10G (24GB VRAM)
- Quantized models where possible:
  - LLM: 4-bit quantization (~4GB)
  - STT: FP16 (~1GB)
  - TTS: FP16 (~1GB)
  - **Total: ~6GB** (plenty of headroom)

**Model Loading:**
- Load all models at startup
- Keep in memory (warm GPU)
- Reset conversation state per session

### Error Handling

- **STT failures**: Fallback to retry or return error
- **LLM failures**: Return error message via TTS
- **TTS failures**: Return text transcript
- **Network issues**: Graceful degradation

### Advantages of Single App

1. **Low Latency**: No network hops between components
2. **Shared Memory**: Models can share GPU efficiently
3. **Atomic Operations**: All-or-nothing processing
4. **Simpler Deployment**: One endpoint, one service
5. **Cost Efficient**: Single GPU for all operations
6. **Easier Debugging**: All logs in one place

### Disadvantages

1. **GPU Memory**: Need enough VRAM for all models
2. **Cold Start**: All models load together (~60s)
3. **Scaling**: One GPU per conversation (can use multiple GPUs)
4. **Complexity**: More code in one file

### Implementation Steps

1. **Create integrated Modal app** (`integrated_voice_agent.py`)
2. **Load Faster-Whisper** for STT
3. **Connect to vLLM** or load Qwen2.5-7B directly
4. **Load VibeVoice** for TTS
5. **Implement streaming pipeline** with async loops
6. **Add error handling** and fallbacks
7. **Test latency** and optimize
8. **Deploy and monitor**

### Alternative: Hybrid Approach

If single app is too complex, use:
- **STT + LLM** in one app (text-based)
- **TTS** in separate app (can be cached/warmed separately)

This reduces complexity while still minimizing latency.

### Next Steps

1. Review this plan
2. Decide on exact models (Faster-Whisper + Qwen2.5-7B + VibeVoice)
3. Implement integrated app
4. Test and benchmark latency
5. Deploy and iterate
