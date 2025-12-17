# Quick Start - Step 3: Chat with vLLM Server

## Get Your Server URL

After running `modal deploy vllm_server.py`, you should see output like:

```
🚀 vLLM Server Deployed!
📡 Server URL: https://your-workspace--vllm-therapist-serve.modal.run
```

**Copy that URL!**

## Option 1: Set URL and Chat (One Command)

```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest && \
source venv/bin/activate && \
export VLLM_SERVER_URL=https://your-workspace--vllm-therapist-serve.modal.run && \
python3 chat_vllm.py
```

**Replace `your-workspace` with your actual Modal workspace name!**

## Option 2: Set URL Once, Chat Multiple Times

**Terminal 1 - Set the URL:**
```bash
export VLLM_SERVER_URL=https://your-workspace--vllm-therapist-serve.modal.run
```

**Terminal 2 - Chat anytime:**
```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest
source venv/bin/activate
python3 chat_vllm.py
```

## Option 3: Use the Helper Script

```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest
source venv/bin/activate
./start_chat.sh
```

## Find Your URL If You Lost It

1. **Modal Dashboard:**
   - Go to https://modal.com/apps
   - Click on `vllm-therapist`
   - Copy the URL shown

2. **From Terminal:**
   ```bash
   modal app show vllm-therapist
   ```
   Look for the URL in the output.

## Single Message (Non-Interactive)

```bash
export VLLM_SERVER_URL=https://your-workspace--vllm-therapist-serve.modal.run
python3 chat_vllm.py "I feel anxious about work"
```

## Make URL Persistent (Optional)

Add to your `~/.zshrc` or `~/.bashrc`:
```bash
export VLLM_SERVER_URL=https://your-workspace--vllm-therapist-serve.modal.run
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

