# Hugging Face Space Setup Guide

## Quick Start

1. **Create a new Space on Hugging Face:**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Name it: `qwen-therapist-chatbot` (or your choice)
   - Select **Gradio** as the SDK
   - Set visibility to **Public**
   - Click "Create Space"

2. **Upload files to your Space:**
   - Upload `app.py` to the root
   - Upload `requirements.txt` (create it with dependencies)
   - Upload `README.md` (optional, for Space description)

3. **Set Environment Variable:**
   - In your Space settings, add a secret:
     - Key: `VLLM_SERVER_URL`
     - Value: `https://whataidea--vllm-therapist-serve.modal.run`
   - Or update `app.py` to use your server URL directly

4. **That's it!** Your Space will build and deploy automatically.

## Files Needed

### `app.py`
The main Gradio application (already created for you)

### `requirements.txt`
```
gradio>=4.0.0
openai>=1.0.0
```

### `README.md` (for Space)
```markdown
---
title: Qwen2.5-7B Therapist Chatbot
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
---

# Qwen2.5-7B Therapist Chatbot

A fine-tuned language model for therapeutic conversations, powered by Modal.ai vLLM.

[View the model](https://huggingface.co/YOUR_USERNAME/qwen2.5-7b-therapist)
```

## Alternative: Self-Hosted Inference

If you want the Space to run inference locally (without Modal), you can modify `app.py` to load the model directly from Hugging Face. However, this requires:
- GPU support in the Space (paid feature)
- Larger model loading time
- More resources

The current setup uses Modal for fast, scalable inference.

