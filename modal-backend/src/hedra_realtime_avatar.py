"""
Modal app for Hedra Realtime Avatar agent.

This agent uses:
- OpenAI Realtime API (integrated STT/LLM/TTS)
- Hedra AvatarSession (video rendering)
- Silero VAD (voice activity detection)
- LiveKit for WebRTC connections

Run locally (starts worker on Modal GPU):
    modal run src.hedra_realtime_avatar:main

Deploy to Modal:
    modal deploy src.hedra_realtime_avatar
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

import modal

# LiveKit + Agents imports
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    AutoSubscribe,
)
from livekit.agents import hedra
from livekit.agents.vad import silero
from livekit.agents.llm import openai as lk_openai

from PIL import Image

# Import config utilities (optional, for validation)
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hedra_realtime_avatar_config import (
        HedraAvatarConfig,
        AvatarImageLoader,
        print_config_status,
    )
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False
    print("⚠️  Config utilities not available, using basic validation")


# ---------- Modal app configuration ----------

# Import shared app from common.py
from .common import app as base_app

# Create stub with specific name for this agent
stub = modal.Stub("hedra-realtime-avatar-agent")

# Build Modal image with required dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "livekit-agents>=1.0.0",
        "livekit-rtc>=1.0.0",
        "pillow>=10.0.0",
        # OpenAI Realtime is included in livekit-agents
    )
)

# GPU configuration - adjust based on your needs
GPU = modal.gpu.A10G()  # Options: A10G, A100, T4


# ---------- Agent definition ----------

class StaticAvatarAgent(Agent):
    """
    Simple avatar agent with static image.
    
    Customize the instructions to change agent behavior:
    """
    
    def __init__(self) -> None:
        super().__init__(
            instructions=os.environ.get(
                "AGENT_INSTRUCTIONS",
                "You are a helpful voice AI assistant with a visual avatar. "
                "Speak naturally and be engaging in conversation."
            )
        )


# ---------- Avatar image loading ----------

def _load_avatar_image() -> Image.Image:
    """
    Load avatar image from the modal-backend directory.
    
    Searches for avatar.png, avatar.jpg, avatar.jpeg in order.
    Uses config utilities if available for validation.
    
    Returns:
        PIL Image object
        
    Raises:
        FileNotFoundError: If no avatar image found
    """
    # Get the modal-backend directory (parent of src/)
    base_dir = Path(__file__).resolve().parent.parent
    
    if HAS_CONFIG:
        try:
            # Use config utility for loading and validation
            return AvatarImageLoader.load_avatar_image(base_dir)
        except Exception as e:
            print(f"⚠️  Config utility error: {e}")
            print("Falling back to basic image loading...")
    
    # Fallback: basic image loading
    for name in ("avatar.png", "avatar.jpg", "avatar.jpeg"):
        candidate = base_dir / name
        if candidate.exists():
            print(f"✅ Loaded avatar image: {candidate}")
            return Image.open(candidate)
    
    raise FileNotFoundError(
        f"No avatar image found in {base_dir}\n"
        "Please provide avatar.png, avatar.jpg, or avatar.jpeg in the modal-backend/ directory."
    )


# ---------- Agent session setup ----------

async def _run_realtime_avatar_job(job_context: JobContext) -> None:
    """
    Core Hedra Realtime Avatar flow.
    
    This function runs for each LiveKit room connection:
    1. Load avatar image
    2. Create Hedra AvatarSession (video participant)
    3. Create AgentSession with OpenAI RealtimeModel + Silero VAD
    4. Start avatar session and agent session
    5. Send initial greeting
    
    Args:
        job_context: LiveKit job context with room information
    """
    print(f"🎭 Starting avatar agent for room: {job_context.room.name}")
    
    try:
        # 1. Load avatar image
        print("📷 Loading avatar image...")
        avatar_image = _load_avatar_image()
        
        # 2. Get room reference
        room: rtc.Room = job_context.room
        print(f"🏠 Room: {room.name}, Participants: {len(room.remote_participants)}")
        
        # 3. Create Hedra AvatarSession
        avatar_identity = HedraAvatarConfig.get_avatar_identity() if HAS_CONFIG else "static-avatar"
        print(f"👤 Avatar identity: {avatar_identity}")
        
        avatar_session = hedra.AvatarSession(
            avatar_participant_identity=avatar_identity,
            avatar_image=avatar_image,
        )
        
        # 4. Configure OpenAI Realtime model
        openai_config = (
            HedraAvatarConfig.get_openai_config() 
            if HAS_CONFIG 
            else {"api_key": os.environ["OPENAI_API_KEY"], "model": "gpt-4o-realtime-preview"}
        )
        
        model = lk_openai.realtime.RealtimeModel(
            model=openai_config["model"],
            api_key=openai_config["api_key"],
        )
        print(f"🤖 Using model: {openai_config['model']}")
        
        # 5. Configure VAD (voice activity detection)
        print("🎤 Loading Silero VAD...")
        vad = silero.VAD.load()
        
        # 6. Create agent session
        session = AgentSession(
            agent=StaticAvatarAgent(),
            llm=model,
            vad=vad,
        )
        
        # 7. Start the avatar session (creates video participant in room)
        print("🎬 Starting avatar session...")
        await avatar_session.start(session, room=room)
        
        # 8. Start handling conversation
        print("✅ Avatar agent ready!")
        await session.start()
        
        # 9. Send initial greeting (optional)
        initial_greeting = os.environ.get(
            "INITIAL_GREETING",
            "Hi there! I am your virtual avatar assistant. How can I help you today?"
        )
        await session.say(initial_greeting)
        
        print("💬 Sent initial greeting")
        
    except Exception as e:
        print(f"❌ Error in avatar agent: {e}")
        import traceback
        traceback.print_exc()
        raise


# ---------- Modal GPU worker entrypoint ----------

@stub.function(
    image=image,
    gpu=GPU,
    concurrency_limit=10,  # Max concurrent sessions per GPU
    keep_warm=1,           # Keep 1 GPU instance warm (reduce cold starts)
    timeout=60 * 60,       # 1 hour timeout per session
    secrets=[
        modal.Secret.from_name("livekit-config", create_if_missing=False),
        modal.Secret.from_name("openai-key", create_if_missing=False),
    ],
)
async def run_worker():
    """
    GPU-powered LiveKit worker that hosts the Hedra Realtime Avatar agent.
    
    This function runs as a long-lived process on Modal:
    - Connects to LiveKit cloud server
    - Listens for room connections
    - Spawns avatar agents for each room
    
    Required Modal secrets:
    - livekit-config: LIVEKIT_WS_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
    - openai-key: OPENAI_API_KEY
    
    Or set environment variables directly (less secure):
    - LIVEKIT_WS_URL
    - LIVEKIT_API_KEY
    - LIVEKIT_API_SECRET
    - OPENAI_API_KEY
    """
    print("🚀 Starting Hedra realtime avatar worker on Modal GPU...")
    
    # Validate configuration (if config utilities available)
    if HAS_CONFIG:
        try:
            print_config_status()
        except Exception as e:
            print(f"⚠️  Config status check failed: {e}")
    
    # Get LiveKit configuration
    if HAS_CONFIG:
        try:
            lk_config = HedraAvatarConfig.get_livekit_config()
            lk_url = lk_config["ws_url"]
            lk_api_key = lk_config["api_key"]
            lk_api_secret = lk_config["api_secret"]
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            raise
    else:
        # Fallback: direct environment variable access
        lk_url = os.environ.get("LIVEKIT_WS_URL")
        lk_api_key = os.environ.get("LIVEKIT_API_KEY")
        lk_api_secret = os.environ.get("LIVEKIT_API_SECRET")
        
        if not all([lk_url, lk_api_key, lk_api_secret]):
            raise ValueError(
                "Missing LiveKit configuration. Set LIVEKIT_WS_URL, "
                "LIVEKIT_API_KEY, and LIVEKIT_API_SECRET environment variables "
                "or Modal secrets."
            )
    
    print(f"🔗 Connecting to LiveKit: {lk_url}")
    
    # Configure worker options
    worker_opts = WorkerOptions(
        auto_subscribe=AutoSubscribe.AUDIO_ONLY,  # Avatar video is outbound
        job_handler=_run_realtime_avatar_job,      # Handler for each room
    )
    
    # Start the LiveKit Agents worker loop (blocks forever)
    print("✅ Worker configured. Waiting for room connections...")
    await cli.run_app(
        lk_url,
        lk_api_key,
        lk_api_secret,
        worker_opts,
    )


# ---------- Local entrypoint (for testing) ----------

@stub.local_entrypoint()
def main():
    """
    Local dev entrypoint.
    
    This starts the GPU worker on Modal remotely.
    The worker will connect to LiveKit and wait for room connections.
    
    To test:
    1. Run this: modal run src.hedra_realtime_avatar:main
    2. Connect to a LiveKit room from your frontend
    3. The avatar should appear in the room
    
    Note: This blocks until the worker stops.
    """
    print("=" * 60)
    print("Hedra Realtime Avatar Agent")
    print("=" * 60)
    print()
    print("Starting worker on Modal GPU...")
    print("Connect to a LiveKit room to see the avatar in action.")
    print()
    
    # Start the worker (remote on Modal)
    run_worker.remote()
    
    print()
    print("Worker started successfully!")
    print("Check Modal logs: modal logs hedra-realtime-avatar-agent --follow")
    print()

