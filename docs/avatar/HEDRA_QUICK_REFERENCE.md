# Hedra Realtime Avatar - Quick Reference

Quick commands and setup checklist for getting started with the Hedra Realtime Avatar system.

## Quick Setup Checklist

### 1. Prerequisites
- [ ] Modal account and CLI installed (`pip install modal && modal setup`)
- [ ] LiveKit Cloud account ([cloud.livekit.io](https://cloud.livekit.io))
- [ ] OpenAI API key with Realtime API access

### 2. LiveKit Setup
- [ ] Create LiveKit project
- [ ] Get WebSocket URL: `wss://your-project.livekit.cloud`
- [ ] Get API Key and API Secret from dashboard

### 3. Modal Configuration
- [ ] Create Modal secrets:
  ```bash
  modal secret create livekit-config \
    LIVEKIT_WS_URL=wss://your-project.livekit.cloud \
    LIVEKIT_API_KEY=your-key \
    LIVEKIT_API_SECRET=your-secret
  
  modal secret create openai-key \
    OPENAI_API_KEY=sk-...
  ```
- [ ] Place avatar image in `modal-backend/avatar.png` (or .jpg/.jpeg)

### 4. Deploy Agent
```bash
cd modal-backend
modal deploy src.hedra_realtime_avatar
```

### 5. Frontend Setup
- [ ] Install LiveKit SDK: `npm install livekit-client livekit-react`
- [ ] Create `/api/avatar/room-token` endpoint
- [ ] Add environment variables to `.env.local`
- [ ] Create avatar page component

## Common Commands

### Modal Commands
```bash
# Deploy agent
modal deploy src.hedra_realtime_avatar

# Run locally (for testing)
modal run src.hedra_realtime_avatar:main

# View logs
modal logs hedra-realtime-avatar-agent --follow

# List secrets
modal secret list

# Create/update secrets
modal secret create livekit-config ...
modal secret update livekit-config ...
```

### Configuration Check
```bash
# Check configuration status
cd modal-backend
python hedra_realtime_avatar_config.py
```

### Testing
```bash
# Test Modal deployment
modal run src.hedra_realtime_avatar:main

# Test frontend locally
npm run dev
# Navigate to http://localhost:3000/avatar
```

## Environment Variables

### Modal Secrets (Required)
```bash
# livekit-config secret:
LIVEKIT_WS_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# openai-key secret:
OPENAI_API_KEY=sk-...
```

### Frontend (.env.local)
```env
# Server-side (for token generation)
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Client-side (public, safe)
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
```

## File Structure

```
modal-backend/
├── src/
│   ├── hedra_realtime_avatar.py  # Main agent
│   └── common.py                  # Shared Modal app
├── avatar.png                     # Avatar image (required)
├── hedra_realtime_avatar_config.py  # Config utilities
├── HEDRA_REALTIME_AVATAR_SETUP.md  # Full guide
└── HEDRA_QUICK_REFERENCE.md       # This file
```

## Troubleshooting Quick Fixes

### Avatar not appearing
1. Check avatar image exists: `ls modal-backend/avatar.*`
2. Check Modal logs: `modal logs hedra-realtime-avatar-agent --follow`
3. Verify LiveKit room has avatar participant (check dashboard)

### Connection errors
1. Verify secrets: `modal secret list`
2. Test LiveKit URL is accessible
3. Check room token is valid (not expired)

### High latency
1. Use `keep_warm=1` in Modal function (already set)
2. Choose same region for LiveKit and Modal
3. Reduce avatar image size (< 1MB recommended)

### Audio not working
1. Check browser microphone permissions
2. Verify OpenAI API key is valid
3. Check LiveKit participant audio tracks in dashboard

## Cost Estimates

**Per concurrent user session:**
- Modal GPU (A10G): ~$0.75/hour when active
- LiveKit: ~$0.001-0.002/minute per participant

**Monthly estimate (10 concurrent users, 1 hour/day):**
- Modal: ~$22.50/month
- LiveKit: ~$50-100/month
- **Total: ~$75-125/month**

## Resources

- **Full Guide**: `HEDRA_REALTIME_AVATAR_SETUP.md`
- **LiveKit Docs**: [docs.livekit.io](https://docs.livekit.io)
- **Modal Docs**: [modal.com/docs](https://modal.com/docs)
- **Hedra Docs**: [docs.hedra.com](https://docs.hedra.com)

