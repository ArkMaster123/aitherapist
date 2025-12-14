"""
vLLM server with OpenAI-compatible API + Function Calling support
Deploy: modal deploy vllm_server_with_tools.py

This enables function calling (tool use) for your fine-tuned therapist model!
"""
import modal

MINUTES = 60
VLLM_PORT = 8000

# vLLM image with CUDA support
vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.11.2",
        "huggingface-hub==0.36.0",
        "flashinfer-python==0.5.2",
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)

app = modal.App("vllm-therapist-tools")

# Model info
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
LORA_PATH = "/data/qwen_therapist_lora"

# Volumes for caching
hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

FAST_BOOT = True
N_GPU = 1

@app.function(
    image=vllm_image,
    gpu=f"A10G:{N_GPU}",
    scaledown_window=15 * MINUTES,
    min_containers=1,  # Keep at least 1 container warm to avoid cold starts
    timeout=10 * MINUTES,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/data": training_volume,
    },
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=VLLM_PORT, startup_timeout=10 * MINUTES)
def serve():
    """Start vLLM server with function calling enabled"""
    import subprocess
    import os
    
    # Check for merged model
    merged_model_path = "/data/qwen_therapist_merged"
    
    if os.path.exists(merged_model_path):
        print(f"✅ Using merged model at {merged_model_path}")
        model_to_serve = merged_model_path
    elif os.path.exists(LORA_PATH):
        print(f"⚠️  LoRA found but not merged. Run: modal run merge_lora_for_vllm.py")
        print(f"   Using base model for now: {MODEL_NAME}")
        model_to_serve = MODEL_NAME
    else:
        print(f"⚠️  Using base model: {MODEL_NAME}")
        model_to_serve = MODEL_NAME
    
    cmd = [
        "vllm",
        "serve",
        "--uvicorn-log-level=info",
        model_to_serve,
        "--served-model-name",
        "qwen-therapist",
        "--host",
        "0.0.0.0",
        "--port",
        str(VLLM_PORT),
        "--tensor-parallel-size",
        str(N_GPU),
        # Enable function calling!
        "--enable-auto-tool-choice",
        "--tool-call-parser",
        "hermes",  # Qwen uses Hermes format for tool calls
    ]
    
    if FAST_BOOT:
        cmd.append("--enforce-eager")
    
    print("Starting vLLM server with function calling enabled...")
    print("Command:", " ".join(cmd))
    
    subprocess.Popen(" ".join(cmd), shell=True)

@app.local_entrypoint()
def main():
    """Test the server"""
    url = serve.get_web_url()
    print("="*70)
    print("🚀 vLLM Server with Function Calling Deployed!")
    print("="*70)
    print(f"\n📡 Server URL: {url}")
    print(f"📚 API Docs: {url}/docs")
    print(f"🏥 Health Check: {url}/health")
    print("\n" + "="*70)
    print("💡 Function Calling Enabled!")
    print("="*70)
    print("\nYou can now use tools/functions in your API calls.")
    print("See test_function_calling.py for examples!")

