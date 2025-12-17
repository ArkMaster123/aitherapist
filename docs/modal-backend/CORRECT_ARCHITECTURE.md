# Correct Architecture: Groq STT (Frontend) + Modal (LLM+TTS)

## Architecture Overview

```
Frontend (Next.js)
  ↓
1. User speaks → Record audio
  ↓
2. Call Groq API (external) → Get transcript
  ↓
3. Send transcript to Modal app → LLM + TTS
  ↓
4. Receive audio response → Play to user
```

## Components

### Frontend (Next.js)
- **STT**: Calls Groq API directly (`/api/groq-stt`)
- **Audio Recording**: Captures user speech
- **WebSocket**: Sends transcript to Modal, receives audio

### Modal App (`llm_tts_agent.py`)
- **LLM**: Qwen2.5-7B via vLLM (300-500ms)
- **TTS**: Cartesia (40ms) or Kokoro (97ms)
- **No STT**: Groq handles that externally!

## Why This is Better

1. **Groq is external API** - No need to run it in Modal
2. **Frontend handles STT** - Can process while user speaks
3. **Modal only does LLM+TTS** - Simpler, faster
4. **Lower latency** - Groq processes in parallel with user speaking

## Performance

- **Groq STT**: ~631ms for 5-sec audio (but processes while user speaks!)
- **LLM**: 300-500ms (streaming)
- **TTS**: 40ms (Cartesia) or 97ms (Kokoro)
- **Effective latency**: ~340-540ms after user stops speaking

## Files

1. `app/api/groq-stt/route.ts` - Frontend API route for Groq STT
2. `modal-backend/src/llm_tts_agent.py` - Modal app (LLM + TTS only)
3. Frontend page - Calls Groq, then Modal

## Setup

1. **Set GROQ_API_KEY** in `.env.local`:
   ```
   GROQ_API_KEY=your-groq-key
   ```

2. **Deploy Modal app**:
   ```bash
   modal deploy -m src.llm_tts_agent
   ```

3. **Optional: Cartesia for 40ms TTS**:
   ```bash
   modal secret create cartesia-api CARTESIA_API_KEY=your-key
   ```

## Flow

1. User speaks → Frontend records audio
2. Frontend → Groq API → Transcript
3. Frontend → Modal WebSocket → Transcript
4. Modal → LLM → Response text
5. Modal → TTS → Audio
6. Modal → Frontend → Audio playback

This is the correct architecture! 🎯
