# Server Management Guide

## Starting the Server

```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest
source venv/bin/activate
modal deploy vllm_server.py
```

The server will:
- Start automatically when you deploy
- Stay alive for 15 minutes after the last request
- Scale down automatically to save costs

## Stopping the Server

### Option 1: Use the script (easiest)
```bash
./STOP_SERVER.sh
```

### Option 2: Manual stop
```bash
modal app stop vllm-therapist
```

### Option 3: Let it scale down
- The server automatically scales down after 15 minutes of inactivity
- No action needed - it will stop on its own

## Checking Server Status

```bash
# List all apps
modal app list

# Check specific app
modal app show vllm-therapist

# View logs
modal app logs vllm-therapist
```

## Cost Management

- **Auto-scaling**: Server scales down after 15 minutes of inactivity
- **Pay per use**: You only pay when the server is running
- **Estimated cost**: ~$0.50-1.00/hour when active (A10G GPU)
- **Free tier**: Modal has a free tier with credits

## Restarting After Stop

Just deploy again:
```bash
modal deploy vllm_server.py
```

The server will start fresh and be ready in ~2-3 minutes.

