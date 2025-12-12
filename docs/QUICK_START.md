# Quick Start - Local CLI Chat

## Full Command

**Interactive mode (keeps connection open):**
```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest && source venv/bin/activate && python3 chat.py
```

**Single message:**
```bash
cd /Users/noahsark/Documents/vibecoding/finetuningtest && source venv/bin/activate && python3 chat.py "your message here"
```

## How It Works

1. **First call**: Creates Modal container, loads model (~30-60 seconds)
2. **All subsequent calls**: Reuses SAME container, model already loaded (2-5 seconds)
3. **Container stays alive**: 5 minutes of inactivity before shutdown

## What Happens

- `chat.py` runs locally on your machine
- Connects to Modal once with `app.run()`
- Creates `TherapistModel()` instance ONCE
- All calls to `model.get_response.remote()` reuse the SAME container
- Model stays loaded in memory - fast responses!

## Model Info

- **Base Model**: Qwen/Qwen2.5-7B-Instruct
- **Fine-tuned LoRA**: `/data/qwen_therapist_lora` on Modal volume
- **GPU**: A10G (24GB VRAM)
- **Container**: Stays alive for 5 minutes (`scaledown_window=300`)

## Troubleshooting

**Slow first response?**
- Normal! Model loads on first call (~30-60 seconds)

**Slow subsequent responses?**
- Should be fast (2-5 seconds). If slow, container might have shut down.
- Check Modal dashboard: https://modal.com/apps

**Connection errors?**
- Make sure Modal is authenticated: `modal token current`
- Check you're in the right directory

