"""
vLLM server with OpenAI-compatible API for fine-tuned Qwen2.5-7B-Instruct.
Deploy: modal deploy vllm_server.py
Access: https://your-workspace--vllm-therapist.modal.run

This provides a standard OpenAI-compatible API that's much faster than our previous approach!
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
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})  # faster model transfers
)

app = modal.App("vllm-therapist")

# Model info
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
LORA_PATH = "/data/qwen_therapist_lora"  # Your fine-tuned LoRA adapter

# Volumes for caching
hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

# Fast boot for quick cold starts
FAST_BOOT = True
N_GPU = 1

@app.function(
    image=vllm_image,
    gpu=f"A10G:{N_GPU}",  # A10G is fine for 7B model
    scaledown_window=15 * MINUTES,  # Stay alive for 15 minutes
    timeout=10 * MINUTES,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/data": training_volume,  # For LoRA adapter
    },
    secrets=[modal.Secret.from_name("huggingface-secret")],  # For HF access
)
@modal.concurrent(max_inputs=32)  # Handle 32 concurrent requests
@modal.web_server(port=VLLM_PORT, startup_timeout=10 * MINUTES)
def serve():
    """Start vLLM server - uses merged model if available"""
    import subprocess
    import os
    
    # Check for merged model (created by merge_lora_for_vllm.py)
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
        # Enable function calling for tool support
        "--enable-auto-tool-choice",
        "--tool-call-parser",
        "hermes",  # Qwen2.5-7B-Instruct uses Hermes parser format for tool calls
    ]
    
    # Fast boot settings
    if FAST_BOOT:
        cmd.append("--enforce-eager")  # Disable compilation for faster startup
    else:
        cmd.append("--no-enforce-eager")  # Enable compilation for better performance
    
    print("Starting vLLM server with command:")
    print(" ".join(cmd))
    
    # Start server
    subprocess.Popen(" ".join(cmd), shell=True)

@app.local_entrypoint()
def main():
    """Test the server"""
    url = serve.get_web_url()
    print("="*70)
    print("🚀 vLLM Server Deployed!")
    print("="*70)
    print(f"\n📡 Server URL: {url}")
    print(f"📚 API Docs: {url}/docs")
    print(f"🏥 Health Check: {url}/health")
    print("\n" + "="*70)
    print("💡 Usage Examples:")
    print("="*70)
    print("\n1. Health check:")
    print(f"   curl {url}/health")
    print("\n2. Chat completion (Python):")
    print("""
from openai import OpenAI

client = OpenAI(
    base_url=f"{url}/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="qwen-therapist",
    messages=[
        {"role": "user", "content": "I feel anxious"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
""")
    print("\n3. Chat completion (curl):")
    print(f"""
curl {url}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{{"model": "qwen-therapist", "messages": [{{"role": "user", "content": "I feel anxious"}}]}}'
""")

