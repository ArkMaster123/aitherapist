# Hedra Avatar Implementation Options

Complete guide to different approaches for implementing Hedra realtime avatar with your existing infrastructure.

## Quick Decision Tree

```
Need lowest latency?
├─ Yes → Option 1: OpenAI Realtime API
└─ No → Use existing vLLM?
    ├─ Yes → Option 2: Pipeline with vLLM
    └─ No → Option 1: OpenAI Realtime API
```

## Option Comparison

| Feature | Option 1: Realtime API | Option 2: Pipeline (vLLM) | Moshi (Not Compatible) |
|---------|----------------------|---------------------------|------------------------|
| **Latency** | ~200-400ms (lowest) | ~700-1000ms (higher) | ~150ms (but no avatar) |
| **Cost** | OpenAI API per minute | vLLM GPU time only | GPU time only |
| **Setup Complexity** | Simple (2 components) | Moderate (3-4 components) | N/A |
| **Uses Your vLLM** | ❌ No | ✅ Yes | ❌ No |
| **Uses Moshi** | ❌ No | ❌ No | ⚠️ Different protocol |
| **Avatar Video** | ✅ Yes | ✅ Yes | ❌ No (voice only) |
| **Provider Flexibility** | ❌ OpenAI only | ✅ Mix providers | ❌ Custom only |

---

## Option 1: OpenAI Realtime API (Current Implementation)

**Best for**: Lowest latency, simplest setup, production-ready

### Architecture

```
Frontend (LiveKit) → LiveKit Cloud → Modal Worker
                                          ├─ Hedra AvatarSession (video)
                                          ├─ OpenAI RealtimeModel (STT+LLM+TTS)
                                          └─ Silero VAD (voice detection)
```

### File Locations

#### Backend Files
- **Agent Implementation**: `modal-backend/src/hedra_realtime_avatar.py`
- **Configuration Utils**: `modal-backend/hedra_realtime_avatar_config.py`
- **Setup Guide**: `modal-backend/HEDRA_REALTIME_AVATAR_SETUP.md`
- **Quick Reference**: `modal-backend/HEDRA_QUICK_REFERENCE.md`

#### Frontend Files (To Create)
- **Avatar Page**: `app/avatar/page.tsx` (not yet created, similar to `app/voice/page.tsx`)
- **Room Token API**: `app/api/avatar/room-token/route.ts` (not yet created)

#### Environment Variables
- **Modal Secrets**: `livekit-config` (LIVEKIT_WS_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
- **Modal Secrets**: `openai-key` (OPENAI_API_KEY)
- **Frontend .env.local**: `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `NEXT_PUBLIC_LIVEKIT_URL`

#### Avatar Image
- **Location**: `modal-backend/avatar.png` (or .jpg/.jpeg)
- **Required**: Yes, must exist before deployment

### Deployment

```bash
# Deploy agent
cd modal-backend
modal deploy src.hedra_realtime_avatar

# Check status
modal logs hedra-realtime-avatar-agent --follow
```

### Pros
- ✅ Lowest latency (~200-400ms total)
- ✅ Simplest setup (only 2 components: RealtimeModel + VAD)
- ✅ Integrated model (no pipeline overhead)
- ✅ Production-ready code already written

### Cons
- ❌ Requires OpenAI API key (paid service)
- ❌ Can't use your existing vLLM server
- ❌ Less flexible (locked to OpenAI)

### When to Use
- Need lowest possible latency
- Don't mind OpenAI API costs
- Want simplest setup
- Production deployment

---

## Option 2: Pipeline with vLLM (To Be Implemented)

**Best for**: Using existing vLLM, avoiding OpenAI costs, provider flexibility

### Architecture

```
Frontend (LiveKit) → LiveKit Cloud → Modal Worker
                                          ├─ Hedra AvatarSession (video)
                                          ├─ STT (Faster-Whisper or Groq)
                                          ├─ LLM (your vLLM server)
                                          ├─ TTS (Kokoro or Cartesia)
                                          └─ Silero VAD (voice detection)
```

### File Locations (To Create)

#### Backend Files
- **Agent Implementation**: `modal-backend/src/hedra_pipeline_avatar.py` ⚠️ **NOT YET CREATED**
- **Configuration**: Can reuse `modal-backend/hedra_realtime_avatar_config.py`
- **Setup Guide**: `modal-backend/HEDRA_PIPELINE_SETUP.md` ⚠️ **NOT YET CREATED**

#### Existing Files to Reference
- **LLM+TTS Agent**: `modal-backend/src/llm_tts_agent.py` (shows vLLM integration)
- **Groq Agent**: `modal-backend/src/groq_ultra_fast_agent.py` (shows STT integration)
- **Common App**: `modal-backend/src/common.py`

#### Frontend Files
- **Same as Option 1**: `app/avatar/page.tsx`, `app/api/avatar/room-token/route.ts`

#### Environment Variables
- **Modal Secrets**: `livekit-config` (same as Option 1)
- **Modal Secrets**: `vllm-config` (VLLM_URL) - or use existing setup
- **Modal Secrets** (optional): `groq-api` (GROQ_API_KEY) if using Groq STT
- **Modal Secrets** (optional): `cartesia-api` (CARTESIA_API_KEY) for faster TTS

### Implementation Status

⚠️ **This option needs to be implemented**

Based on:
- `modal-backend/src/llm_tts_agent.py` - vLLM + TTS integration
- `modal-backend/src/groq_ultra_fast_agent.py` - STT + LLM + TTS pipeline
- LiveKit Hedra pipeline examples

### Pros
- ✅ Uses your existing vLLM server (no OpenAI costs)
- ✅ Provider flexibility (can mix STT/TTS providers)
- ✅ Reuses existing infrastructure
- ✅ Lower cost (only GPU time for vLLM)

### Cons
- ❌ Higher latency (~700-1000ms vs ~200-400ms)
- ❌ More complex (3-4 components vs 2)
- ❌ More code to maintain
- ❌ Pipeline overhead (component handoffs)

### When to Use
- Want to use existing vLLM server
- Need to avoid OpenAI API costs
- Want provider flexibility (mix Deepgram, Cartesia, etc.)
- Latency requirements allow ~700-1000ms

---

## Option 3: Moshi (Not Compatible with Hedra)

**Status**: ⚠️ **Cannot be used for Hedra avatar**

### Why Not Compatible?

1. **Different Protocol**: Moshi uses custom WebSocket protocol, Hedra requires LiveKit Agents protocol
2. **No Video**: Moshi is speech-to-speech only, no avatar video rendering
3. **Different Architecture**: Moshi runs as separate WebSocket server, Hedra needs LiveKit agent

### Current Moshi Implementation

#### File Locations
- **Moshi Agent**: `modal-backend/src/moshi.py`
- **Frontend**: `app/voice/page.tsx`
- **API Route**: `app/api/voice/ws-url/route.ts`

#### Protocol
- **Custom WebSocket**: Opus-encoded audio
- **Message Format**: `\x01` (audio), `\x02` (text)
- **No OpenAI compatibility**: Completely custom protocol

### Could Moshi Be Adapted?

**Theoretical approach** (not recommended):
1. Wrap Moshi in LiveKit agent adapter
2. Use Hedra AvatarSession separately
3. Bridge Moshi audio output to Hedra video

**Why Not Recommended**:
- Complex integration
- Moshi already has very low latency (150ms)
- Avatar adds overhead
- Better to use dedicated avatar solution

### When to Use Moshi
- ✅ Voice-only conversations (no avatar needed)
- ✅ Ultra-low latency requirements (150ms)
- ✅ Don't need video/visual component

---

## File Structure Overview

```
modal-backend/
├── src/
│   ├── common.py                           # Shared Modal app
│   ├── hedra_realtime_avatar.py           # ✅ Option 1: Realtime (IMPLEMENTED)
│   ├── hedra_pipeline_avatar.py           # ⚠️ Option 2: Pipeline (TO CREATE)
│   ├── moshi.py                           # ⚠️ Option 3: Moshi (voice only, no avatar)
│   ├── llm_tts_agent.py                   # Reference for vLLM + TTS
│   └── groq_ultra_fast_agent.py           # Reference for STT + LLM + TTS pipeline
│
├── hedra_realtime_avatar_config.py        # ✅ Config utilities (IMPLEMENTED)
├── avatar.png                              # ✅ Avatar image (required for both options)
│
├── HEDRA_REALTIME_AVATAR_SETUP.md         # ✅ Option 1 setup guide (IMPLEMENTED)
├── HEDRA_QUICK_REFERENCE.md               # ✅ Quick reference (IMPLEMENTED)
├── HEDRA_OPTIONS.md                       # ✅ This file (IMPLEMENTED)
└── HEDRA_PIPELINE_SETUP.md                # ⚠️ Option 2 setup guide (TO CREATE)

app/
├── avatar/
│   └── page.tsx                           # ⚠️ Avatar frontend page (TO CREATE)
├── api/
│   └── avatar/
│       └── room-token/
│           └── route.ts                   # ⚠️ Room token API (TO CREATE)
│
└── voice/
    └── page.tsx                           # ✅ Moshi voice page (exists, voice only)

env.example                                # ✅ Environment variables template
```

---

## Migration Paths

### From Option 1 (Realtime) → Option 2 (Pipeline)

1. Create `hedra_pipeline_avatar.py` based on `hedra_realtime_avatar.py`
2. Replace `RealtimeModel` with:
   - STT: `deepgram.STT()` or `faster_whisper.STT()`
   - LLM: `openai.LLM(base_url=vllm_url)` (your vLLM)
   - TTS: `kokoro.TTS()` or `cartesia.TTS()`
3. Update session configuration (add `stt`, `llm`, `tts` params)
4. Test and deploy
5. Update frontend if needed (should be same)

### From Moshi → Hedra Avatar

1. Keep Moshi for voice-only use cases
2. Implement Hedra separately for avatar use cases
3. Frontend can have both `/voice` (Moshi) and `/avatar` (Hedra) pages

### Using Both Options

You can deploy both:
- **Option 1** for low-latency avatar conversations
- **Option 2** for cost-effective avatar conversations
- Choose per room or per use case

---

## Cost Comparison

### Option 1: OpenAI Realtime
- **Modal GPU**: ~$0.75/hour (A10G, scales to $0 when idle)
- **OpenAI API**: ~$0.03-0.06 per minute of conversation
- **LiveKit**: ~$0.001-0.002 per participant minute
- **Estimated (10 users, 1 hour/day)**: ~$75-125/month

### Option 2: Pipeline with vLLM
- **Modal GPU (vLLM)**: Already running, shared cost
- **Modal GPU (Avatar worker)**: ~$0.75/hour (scales to $0 when idle)
- **STT (Groq)**: Free tier or ~$0.001 per minute
- **TTS (Kokoro)**: Free (self-hosted) or Cartesia ~$0.001 per minute
- **LiveKit**: Same as Option 1
- **Estimated (10 users, 1 hour/day)**: ~$25-50/month (much lower)

### Moshi (Voice Only)
- **Modal GPU**: ~$0.75/hour (scales to $0 when idle)
- **No API costs**: Everything self-hosted
- **Estimated (10 users, 1 hour/day)**: ~$22.50/month

---

## Recommendation

### For Production (Avatar Required)
1. **Start with Option 1** (Realtime) - fastest to deploy, lowest latency
2. **Migrate to Option 2** (Pipeline) - if cost becomes a concern

### For Development
- Use **Option 1** for quick testing
- Build **Option 2** in parallel for cost optimization

### For Voice-Only (No Avatar)
- Use **Moshi** - already implemented, lowest latency

---

## Next Steps

### To Implement Option 2 (Pipeline)

1. **Create pipeline agent file**:
   ```bash
   cp modal-backend/src/hedra_realtime_avatar.py modal-backend/src/hedra_pipeline_avatar.py
   ```

2. **Modify to use pipeline components**:
   - Replace `RealtimeModel` with STT + LLM + TTS
   - Reference `llm_tts_agent.py` for vLLM integration
   - Reference `groq_ultra_fast_agent.py` for pipeline pattern

3. **Update configuration**:
   - Add VLLM_URL to config
   - Add STT provider selection
   - Add TTS provider selection

4. **Create setup guide**:
   - Similar structure to `HEDRA_REALTIME_AVATAR_SETUP.md`
   - Document pipeline-specific steps

5. **Test and deploy**

---

## Questions?

- **Want to use vLLM?** → Implement Option 2
- **Want lowest latency?** → Use Option 1
- **Want voice only?** → Use Moshi
- **Want both?** → Deploy multiple agents, choose per use case

