# Why Use Lite Versions? (No Unsloth for Inference)

## The Problem

When you fine-tune with Unsloth, you get:
- ✅ Fast training
- ✅ Optimized LoRA adapters
- ❌ But inference still needs Unsloth to load the model

## The Solution: Lite Versions

**For inference, you don't need:**
- ❌ Unsloth (only needed for training)
- ❌ Training libraries (trl, datasets, tensorboard)
- ❌ Large dependencies (torchvision, xformers for training)

**You only need:**
- ✅ `transformers` - Standard model loading
- ✅ `peft` - LoRA adapter loading
- ✅ `bitsandbytes` - 4-bit quantization
- ✅ `accelerate` - Model loading utilities

## Benefits

1. **Faster startup** - Smaller image, fewer dependencies
2. **Faster builds** - No need to compile Unsloth from git
3. **Smaller images** - Less disk space, faster cold starts
4. **Standard libraries** - Uses Hugging Face's standard tools

## Files

- `streaming_inference_lite.py` - Lightweight streaming API
- `chatbot_cli_lite.py` - Lightweight CLI chatbot

## How It Works

Unsloth saves models in **standard PEFT format**, so you can load them with:

```python
from transformers import AutoModelForCausalLM
from peft import PeftModel

# Load base model
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct", ...)

# Load LoRA adapter (saved by Unsloth)
model = PeftModel.from_pretrained(model, "/data/qwen_therapist_lora")
```

That's it! No Unsloth needed for inference.

## Usage

**Lite CLI Chatbot:**
```bash
modal run chatbot_cli_lite.py
```

**Lite Streaming API:**
```bash
modal deploy streaming_inference_lite.py
```

Both are faster to start and use less resources! 🚀

