# vLLM Server Setup - Fast OpenAI-Compatible API

## Why vLLM?

✅ **Much faster** - Optimized inference engine  
✅ **OpenAI-compatible API** - Standard interface  
✅ **Better throughput** - Handles multiple requests efficiently  
✅ **Production-ready** - Used by many companies  

## Setup Steps

### 1. Merge LoRA Adapter (One-time)

vLLM works best with merged models. Merge your LoRA adapter first:

```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest
source venv/bin/activate
modal run merge_lora_for_vllm.py
```

This creates a merged model at `/data/qwen_therapist_merged` on your Modal volume.

### 2. Deploy vLLM Server

```bash
modal deploy vllm_server.py
```

After deployment, you'll get a URL like:
```
https://your-workspace--vllm-therapist-serve.modal.run
```

### 3. Use from Local CLI

**Set the server URL:**
```bash
export VLLM_SERVER_URL=https://your-workspace--vllm-therapist-serve.modal.run
```

**Run the chat client:**
```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest
source venv/bin/activate
python3 chat_vllm.py
```

Or single message:
```bash
python3 chat_vllm.py "I feel anxious"
```

## Full Commands

**Merge LoRA (one-time):**
```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest && source venv/bin/activate && modal run merge_lora_for_vllm.py
```

**Deploy server:**
```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest && source venv/bin/activate && modal deploy vllm_server.py
```

**Chat (after setting VLLM_SERVER_URL):**
```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest && source venv/bin/activate && python3 chat_vllm.py
```

## Benefits Over Previous Approach

| Feature | Previous (transformers) | vLLM |
|---------|-------------------------|------|
| Speed | ~2-5 seconds | ~0.5-1 second |
| Throughput | 1 request at a time | 32 concurrent requests |
| API | Custom | OpenAI-compatible |
| Optimization | Basic | Highly optimized |

## Model Info

- **Base Model**: Qwen/Qwen2.5-7B-Instruct
- **Fine-tuned**: Merged LoRA adapter
- **GPU**: A10G (24GB VRAM)
- **API**: OpenAI-compatible (`/v1/chat/completions`)

## API Usage

**Python:**
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-workspace--vllm-therapist-serve.modal.run/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="qwen-therapist",
    messages=[{"role": "user", "content": "I feel anxious"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**curl:**
```bash
curl https://your-workspace--vllm-therapist-serve.modal.run/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-therapist", "messages": [{"role": "user", "content": "I feel anxious"}]}'
```

