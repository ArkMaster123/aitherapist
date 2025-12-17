# 🚀 Quick Reference Card

## Stop Server
```bash
./STOP_SERVER.sh
# or
modal app stop vllm-therapist
```

## Start Server
```bash
modal deploy vllm_server.py
```

## Chat Locally
```bash
export VLLM_SERVER_URL=https://whataidea--vllm-therapist-serve.modal.run
python3 chat_vllm.py
# or
./START_CHAT.sh
```

## Upload Model to Hugging Face
```bash
# 1. Make sure HF token is in Modal secret
modal secret create huggingface-secret HF_TOKEN=your_token

# 2. Upload
modal run upload_model_to_hf.py
```

## Create Hugging Face Space
1. Go to https://huggingface.co/spaces → Create new Space
2. Name: `qwen-therapist-chatbot`, SDK: `Gradio`, Public
3. Upload: `app.py`, `requirements.txt`, `SPACE_README.md` (as README.md)
4. Add secret: `VLLM_SERVER_URL` = `https://whataidea--vllm-therapist-serve.modal.run`
5. Wait for build (~2-3 min)

## Files Created
- ✅ `STOP_SERVER.sh` - Stop Modal server
- ✅ `upload_model_to_hf.py` - Upload model to HF Hub
- ✅ `app.py` - Gradio Space app
- ✅ `requirements.txt` - Space dependencies
- ✅ `SPACE_README.md` - Space description
- ✅ `PUBLISH_GUIDE.md` - Complete publishing guide
- ✅ `SERVER_MANAGEMENT.md` - Server management details

## Your Links (After Publishing)
- **Model**: `https://huggingface.co/YOUR_USERNAME/qwen2.5-7b-therapist`
- **Space**: `https://huggingface.co/spaces/YOUR_USERNAME/qwen-therapist-chatbot`

---

**See `PUBLISH_GUIDE.md` for detailed instructions!**

