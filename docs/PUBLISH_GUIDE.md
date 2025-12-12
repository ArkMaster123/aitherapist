# 🚀 Publishing Guide: Model + Space

Complete guide to publish your fine-tuned therapist model and create a Hugging Face Space!

## Step 1: Upload Model to Hugging Face 🤗

### Prerequisites
- Hugging Face account (sign up at https://huggingface.co)
- Hugging Face token (get it from https://huggingface.co/settings/tokens)

### Setup Modal Secret
```bash
# Create/update your Hugging Face secret in Modal
modal secret create huggingface-secret HF_TOKEN=your_hf_token_here
```

### Upload the Model
```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest
source venv/bin/activate
modal run upload_model_to_hf.py
```

This will:
- ✅ Check for merged model (or merge LoRA if needed)
- ✅ Upload to `your-username/qwen2.5-7b-therapist`
- ✅ Create a model card with usage examples
- ✅ Make it public and shareable

**Time**: ~15-30 minutes (depending on upload speed)

## Step 2: Create Hugging Face Space 🌐

### Option A: Using Web UI (Easiest)

1. **Go to**: https://huggingface.co/spaces
2. **Click**: "Create new Space"
3. **Fill in**:
   - **Name**: `qwen-therapist-chatbot` (or your choice)
   - **SDK**: `Gradio`
   - **Visibility**: `Public`
   - **Hardware**: `CPU basic` (free tier is fine)
4. **Click**: "Create Space"

5. **Upload Files**:
   - Upload `app.py` (drag & drop or use Git)
   - Upload `requirements.txt`
   - Upload `SPACE_README.md` as `README.md`

6. **Set Environment Variable**:
   - Go to Space Settings → Secrets
   - Add secret:
     - **Key**: `VLLM_SERVER_URL`
     - **Value**: `https://whataidea--vllm-therapist-serve.modal.run`
   - Save

7. **Wait for Build**: Space will build automatically (~2-3 minutes)

### Option B: Using Git (Advanced)

```bash
# Clone your Space (after creating it on HF)
git clone https://huggingface.co/spaces/YOUR_USERNAME/qwen-therapist-chatbot
cd qwen-therapist-chatbot

# Copy files
cp /path/to/finetuningtest/app.py .
cp /path/to/finetuningtest/requirements.txt .
cp /path/to/finetuningtest/SPACE_README.md README.md

# Commit and push
git add .
git commit -m "Initial commit: Therapist chatbot"
git push
```

## Step 3: Update Links

After uploading, update these files with your actual username:

1. **`app.py`**: Update model link in Markdown
2. **`SPACE_README.md`**: Replace `YOUR_USERNAME` with your HF username
3. **Model card**: Will be auto-generated, but you can edit it on HF

## Step 4: Share Your Work! 🎉

### Share Links:
- **Model**: `https://huggingface.co/YOUR_USERNAME/qwen2.5-7b-therapist`
- **Space**: `https://huggingface.co/spaces/YOUR_USERNAME/qwen-therapist-chatbot`

### Social Media Template:
```
🚀 Just published my fine-tuned Qwen2.5-7B therapist chatbot!

🧠 Model: https://huggingface.co/YOUR_USERNAME/qwen2.5-7b-therapist
💬 Try it: https://huggingface.co/spaces/YOUR_USERNAME/qwen-therapist-chatbot

Trained on therapist conversations using LoRA fine-tuning on Modal.ai H100 GPUs!

#AI #LLM #FineTuning #HuggingFace
```

## Troubleshooting

### Model Upload Issues
- **Large file timeout**: The script has a 1-hour timeout. If it fails, try uploading in chunks or use `huggingface-cli`
- **Token issues**: Make sure your HF token has write permissions

### Space Issues
- **Build fails**: Check the logs in Space settings
- **Server not responding**: Make sure your Modal server is running
- **Environment variable**: Double-check the `VLLM_SERVER_URL` secret

### Server Management
- **Start server**: `modal deploy vllm_server.py`
- **Stop server**: `./STOP_SERVER.sh` or `modal app stop vllm-therapist`
- **Check status**: `modal app show vllm-therapist`

## Next Steps

1. ✅ Upload model → Get model link
2. ✅ Create Space → Get Space link  
3. ✅ Update links in README files
4. ✅ Share on social media
5. ✅ Add to your portfolio/resume!

## Cost Notes

- **Model Storage**: Free on Hugging Face (up to 50GB)
- **Space**: Free tier available (CPU basic)
- **Modal Server**: Pay-per-use (~$0.50-1.00/hour when active)
  - Auto-scales down after 15 min of inactivity
  - Only pay when Space is being used

---

**Congratulations on your fine-tuned model! 🎉**

