# Configuration Guide for vLLM Server

## Step 1: Start/Deploy Your vLLM Server

Your vLLM server endpoint: `https://whataidea--vllm-therapist-serve.modal.run`

To start it:
```bash
cd scripts
modal deploy vllm_server.py
```

Or if already deployed:
```bash
modal app start vllm-therapist
```

## Step 2: Configure .env.local

Once the server is running, add this to your `.env.local` file:

```env
OPENAI_API_BASE=https://whataidea--vllm-therapist-serve.modal.run
AI_MODEL=llm
OPENAI_API_KEY=not-needed
```

## Step 3: Test the Connection

The endpoint should respond to:
- Health check: `https://whataidea--vllm-therapist-serve.modal.run/health`
- Models list: `https://whataidea--vllm-therapist-serve.modal.run/v1/models`
- Chat completions: `https://whataidea--vllm-therapist-serve.modal.run/v1/chat/completions`

## Troubleshooting

**Server not responding?**
- Check if it's running: `modal app list`
- Start it: `modal app start vllm-therapist`
- Check logs: `modal app logs vllm-therapist`

**Model name?**
- Default vLLM model name is usually `llm`
- Check available models: `curl https://whataidea--vllm-therapist-serve.modal.run/v1/models`

