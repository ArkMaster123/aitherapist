# Hedra Realtime Avatar Setup Guide

Complete guide for setting up a real-time avatar system using Modal, LiveKit, and Hedra with OpenAI's Realtime API.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [LiveKit Setup](#livekit-setup)
- [Modal Backend Configuration](#modal-backend-configuration)
- [Frontend Integration](#frontend-integration)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)

## Architecture Overview

The realtime avatar system uses a three-tier architecture:

```
┌─────────────────┐
│   Next.js       │
│   Frontend      │
│   (LiveKit SDK) │
└────────┬────────┘
         │ WebRTC (audio/video)
         │
┌────────▼────────┐
│   LiveKit       │
│   Cloud Server  │
│   (Room Mgmt)   │
└────────┬────────┘
         │ Agent Protocol
         │
┌────────▼────────────────────────┐
│   Modal GPU Worker              │
│   - Hedra AvatarSession         │
│   - OpenAI RealtimeModel        │
│   - Silero VAD                  │
│   - Video participant           │
└─────────────────────────────────┘
```

### Key Components

1. **Frontend (Next.js)**: 
   - LiveKit React SDK for WebRTC connections
   - Video/audio rendering
   - Room token generation API

2. **LiveKit Cloud**:
   - WebRTC media server
   - Room orchestration
   - Real-time signaling

3. **Modal Backend**:
   - GPU-accelerated avatar rendering (Hedra)
   - Integrated STT/LLM/TTS (OpenAI Realtime)
   - Voice activity detection (Silero VAD)

### Why Realtime Architecture?

- **Low Latency**: Single model call eliminates pipeline overhead (~50% faster than STT→LLM→TTS)
- **Simplified Setup**: 2 components (RealtimeModel + VAD) vs 5-6 in pipeline approach
- **Natural Conversation**: Integrated model provides better turn-taking

## Prerequisites

### Required Accounts & Services

1. **Modal Account**
   - Sign up at [modal.com](https://modal.com)
   - Install CLI: `pip install modal`
   - Authenticate: `modal setup && modal token new`

2. **LiveKit Cloud Account**
   - Sign up at [cloud.livekit.io](https://cloud.livekit.io)
   - Create a project
   - Get WebSocket URL, API Key, and API Secret

3. **OpenAI API Key**
   - Get key from [platform.openai.com](https://platform.openai.com)
   - Required for Realtime API access

### System Requirements

- Python 3.11+
- Node.js 18+ (for frontend)
- Modal CLI installed and authenticated
- GPU quota on Modal (A10G recommended)

## LiveKit Setup

### 1. Create LiveKit Project

1. Go to [cloud.livekit.io](https://cloud.livekit.io)
2. Create a new project
3. Note your project region (e.g., `us`, `eu`)

### 2. Get Credentials

From LiveKit dashboard, copy:
- **WebSocket URL**: `wss://your-project.livekit.cloud`
- **API Key**: Found in "Keys" section
- **API Secret**: Found in "Keys" section (shown once)

### 3. Configure Project Settings

In LiveKit dashboard:
- Enable **TURN servers** (automatic for cloud projects)
- Set **max participants per room**: 2 (user + avatar)
- Enable **E2EE** if needed (optional, adds latency)

### 4. Create API Token (for testing)

For local testing, you can generate tokens:

```bash
# Install LiveKit CLI
pip install livekit-cli

# Generate token (replace with your values)
livekit-cli token create \
  --api-key YOUR_API_KEY \
  --api-secret YOUR_API_SECRET \
  --join \
  --room test-room \
  --identity user-123 \
  --video \
  --audio \
  --publish \
  --subscribe
```

## Modal Backend Configuration

### 1. Project Structure

```
modal-backend/
├── src/
│   ├── hedra_realtime_avatar.py  # Main agent file
│   └── common.py                  # Shared Modal app
├── avatar.png                     # Avatar image (required)
└── HEDRA_REALTIME_AVATAR_SETUP.md
```

### 2. Install Dependencies

The Modal image will handle dependencies, but for local development:

```bash
cd modal-backend
pip install livekit-agents livekit-rtc pillow
```

### 3. Prepare Avatar Image

Place an avatar image in the `modal-backend/` directory:
- Supported formats: `.png`, `.jpg`, `.jpeg`
- Recommended size: 512x512 to 1024x1024
- Square aspect ratio works best
- Name it: `avatar.png`, `avatar.jpg`, or `avatar.jpeg`

### 4. Create Modal Secrets

Set environment variables in Modal:

```bash
# Set LiveKit credentials
modal secret create livekit-secrets \
  LIVEKIT_WS_URL=wss://your-project.livekit.cloud \
  LIVEKIT_API_KEY=your-api-key \
  LIVEKIT_API_SECRET=your-api-secret

# Set OpenAI API key
modal secret create openai-api \
  OPENAI_API_KEY=sk-...
```

Or set in code (less secure):

```python
# In hedra_realtime_avatar.py
import os
os.environ["LIVEKIT_WS_URL"] = "wss://your-project.livekit.cloud"
os.environ["LIVEKIT_API_KEY"] = "your-api-key"
os.environ["LIVEAPI_SECRET"] = "your-api-secret"
os.environ["OPENAI_API_KEY"] = "sk-..."
```

### 5. Modal App Configuration

The agent runs as a long-lived worker that connects to LiveKit:

```python
@stub.function(
    image=image,
    gpu=GPU,
    concurrency_limit=10,  # Max concurrent sessions
    keep_warm=1,            # Keep 1 GPU warm
    timeout=60 * 60,        # 1 hour timeout per session
)
async def run_worker():
    # Worker loop connects to LiveKit
    # Each room connection spawns a new agent session
```

### 6. GPU Selection

- **A10G** (recommended): Balanced performance/cost, ~$0.75/hour
- **A100**: Higher throughput, ~$3.50/hour
- **T4**: Budget option, may struggle with avatar rendering

## Frontend Integration

### 1. Install LiveKit SDK

```bash
npm install livekit-client livekit-react
# or
yarn add livekit-client livekit-react
```

### 2. Create Room Token API

Create `app/api/avatar/room-token/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { AccessToken } from 'livekit-server-sdk';

export async function POST(request: Request) {
  const { roomName, participantName } = await request.json();
  
  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  
  if (!apiKey || !apiSecret) {
    return NextResponse.json(
      { error: 'LiveKit not configured' },
      { status: 500 }
    );
  }
  
  const at = new AccessToken(apiKey, apiSecret, {
    identity: participantName || `user-${Date.now()}`,
  });
  
  at.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
  });
  
  return NextResponse.json({
    token: await at.toJwt(),
  });
}
```

### 3. Create Avatar Page

See `app/avatar/page.tsx` example (similar to `app/voice/page.tsx` but with video):

Key differences:
- Uses `LiveKitRoom` component for video rendering
- Subscribes to avatar participant's video track
- Shows local user video (optional)

### 4. Environment Variables

Add to `.env.local`:

```env
# LiveKit Configuration
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
LIVEKIT_URL=wss://your-project.livekit.cloud

# Modal Configuration (for agent URL if needed)
MODAL_USERNAME=your-modal-username
MODAL_APP_NAME=therapist-voice-chat
```

## Environment Variables

### Modal Secrets

Required for the agent worker:

```bash
# LiveKit connection
LIVEKIT_WS_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# OpenAI Realtime API
OPENAI_API_KEY=sk-...
```

### Frontend Environment Variables

Server-side only (for room token generation):

```env
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
LIVEKIT_URL=wss://your-project.livekit.cloud
```

Client-side (public, safe to expose):

```env
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
```

### Setting Modal Secrets

**Option 1: Modal CLI**

```bash
modal secret create livekit-config \
  LIVEKIT_WS_URL=wss://... \
  LIVEKIT_API_KEY=... \
  LIVEKIT_API_SECRET=...

modal secret create openai-key \
  OPENAI_API_KEY=sk-...
```

**Option 2: Modal Dashboard**

1. Go to [modal.com/apps](https://modal.com/apps)
2. Navigate to your app
3. Go to "Secrets" tab
4. Create secrets with key-value pairs

**Option 3: In Code (Development Only)**

```python
import os
from modal import Secret

stub = modal.Stub("hedra-realtime-avatar-agent")

# Access from environment
@stub.function(secrets=[Secret.from_name("livekit-config")])
async def run_worker():
    url = os.environ["LIVEKIT_WS_URL"]
    # ...
```

## Deployment

### 1. Deploy Modal Worker

```bash
cd modal-backend
modal deploy src.hedra_realtime_avatar:run_worker
```

Or if using a local entrypoint:

```bash
modal deploy src.hedra_realtime_avatar
```

The worker will:
1. Start on Modal GPU
2. Connect to LiveKit cloud
3. Listen for room connections
4. Spawn avatar agents for each room

### 2. Verify Deployment

Check Modal logs:

```bash
modal logs hedra-realtime-avatar-agent
```

You should see:
```
Starting Hedra realtime avatar worker on Modal GPU...
Worker started. Connect via LiveKit (room token) to see the avatar.
```

### 3. Deploy Frontend

```bash
# Build and deploy to Vercel
vercel deploy

# Or run locally
npm run dev
```

### 4. Test Connection Flow

1. Frontend requests room token from `/api/avatar/room-token`
2. Frontend connects to LiveKit room with token
3. Modal worker detects new participant
4. Worker spawns avatar agent (loads image, starts session)
5. Avatar joins room as video participant
6. User sees avatar video and can interact via audio

## Testing

### 1. Local Testing (Modal Worker)

```bash
# Run worker locally (connects to Modal GPU remotely)
modal run src.hedra_realtime_avatar:main
```

### 2. Test LiveKit Connection

```python
# test_livekit.py
import asyncio
from livekit import rtc

async def test_connection():
    room = rtc.Room()
    await room.connect(
        "wss://your-project.livekit.cloud",
        token="your-room-token"
    )
    print("Connected!")
    await room.disconnect()

asyncio.run(test_connection())
```

### 3. Frontend Testing

1. Start dev server: `npm run dev`
2. Navigate to `/avatar`
3. Click "Start Session"
4. Grant camera/microphone permissions
5. Avatar should appear within 5-10 seconds

### 4. Check Logs

**Modal logs:**
```bash
modal logs hedra-realtime-avatar-agent --follow
```

**LiveKit dashboard:**
- Go to project → "Rooms"
- See active rooms and participants
- Check participant video/audio tracks

## Troubleshooting

### Avatar Not Appearing

**Check 1: Avatar Image**
```bash
# Ensure avatar image exists
ls -la modal-backend/avatar.png
```

**Check 2: Modal Logs**
```bash
modal logs hedra-realtime-avatar-agent --follow
```

Look for:
- `FileNotFoundError`: Avatar image not found
- `PermissionError`: Cannot access image
- `ImportError`: Missing dependencies

**Check 3: LiveKit Connection**
- Verify room token is valid
- Check participant list in LiveKit dashboard
- Ensure avatar participant joined (identity: "static-avatar")

### Audio Not Working

**Check 1: Microphone Permissions**
- Browser must allow microphone access
- Check browser console for permission errors

**Check 2: LiveKit Audio Tracks**
- Open browser DevTools → Network → WS
- Check if audio tracks are published/subscribed

**Check 3: OpenAI API Key**
```bash
# Verify secret is set
modal secret list
modal secret show livekit-config  # or openai-key
```

### High Latency

**Optimization 1: GPU Selection**
- Upgrade to A100 for faster inference
- Use `keep_warm=1` to avoid cold starts

**Optimization 2: Region Selection**
- Choose LiveKit region closest to Modal region
- US East → US East (reduce network latency)

**Optimization 3: Avatar Image Size**
- Use smaller images (512x512 vs 1024x1024)
- Reduces GPU memory and processing time

### Modal Worker Not Starting

**Check 1: Secrets**
```bash
modal secret list
# Ensure all required secrets exist
```

**Check 2: GPU Quota**
```bash
# Check GPU availability
modal app list
# If no GPUs available, contact Modal support
```

**Check 3: Image Build**
```bash
# Test image build locally
modal run src.hedra_realtime_avatar:main --detach
```

### LiveKit Connection Errors

**Error: "Invalid token"**
- Token expired (default: 6 hours)
- Regenerate token from API

**Error: "Room not found"**
- Room must be created before connecting
- Or use ephemeral rooms (auto-create on first join)

**Error: "Insufficient permissions"**
- Token must have `canPublish` and `canSubscribe`
- Check token generation code

## Performance Optimization

### 1. GPU Warm Pool

Keep GPUs warm to avoid cold starts:

```python
@stub.function(
    keep_warm=1,  # Keep 1 GPU instance warm
    # ...
)
```

### 2. Concurrency Limits

Balance cost vs responsiveness:

```python
@stub.function(
    concurrency_limit=10,  # Max 10 concurrent sessions per GPU
    # ...
)
```

### 3. Avatar Image Optimization

- Use PNG with transparency for best quality
- Compress images (< 500KB)
- Square aspect ratio (1:1)
- Recommended: 512x512 or 1024x1024

### 4. Network Optimization

- Co-locate LiveKit and Modal in same region
- Use LiveKit's TURN servers (automatic)
- Enable E2EE only if needed (adds latency)

### 5. Cost Optimization

**Modal Costs:**
- A10G: ~$0.75/hour when active
- Scales to $0 when idle (after scaledown_window)
- Only pay for GPU time during sessions

**LiveKit Costs:**
- Pay-per-minute for participant minutes
- Includes video encoding/decoding
- Check [pricing](https://livekit.io/pricing) for details

**Estimated Monthly Cost (10 concurrent users, 1 hour/day):**
- Modal: ~$22.50/month (30 hours × $0.75)
- LiveKit: ~$50-100/month (depends on plan)
- **Total: ~$75-125/month**

## Next Steps

### Customization

1. **Avatar Behavior**: Modify `StaticAvatarAgent.instructions`
2. **Voice**: Adjust OpenAI Realtime model parameters
3. **UI**: Customize frontend with LiveKit React hooks
4. **Features**: Add function tools to agent

### Advanced Features

- **Multiple Avatars**: Spawn different avatars per room
- **Dynamic Avatars**: Generate avatars on-demand (see Hedra docs)
- **Multi-user Rooms**: Support multiple users per room
- **Recording**: Use LiveKit's recording feature

### Resources

- [LiveKit Docs](https://docs.livekit.io)
- [LiveKit Agents Docs](https://docs.livekit.io/agents)
- [Hedra Avatar Docs](https://docs.hedra.com)
- [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- [Modal Docs](https://modal.com/docs)

## Support

For issues:
1. Check [Troubleshooting](#troubleshooting) section
2. Review Modal logs: `modal logs hedra-realtime-avatar-agent`
3. Check LiveKit dashboard for room/participant status
4. Verify all environment variables are set correctly

