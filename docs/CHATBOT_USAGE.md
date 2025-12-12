# Therapist Chatbot CLI - Usage Guide

## Quick Start

Run the chatbot:
```bash
modal run chatbot_cli.py
```

## How to Use

1. **Wait for the model to load** (first time takes ~10-20 seconds)
2. **Type your message** when you see `You: ` prompt
3. **Press Enter** to send
4. **Wait for response** - the model will generate a therapist-style response
5. **Continue chatting** - the conversation history is maintained

## Commands

- **Type your message** - Normal chat
- `quit`, `exit`, or `bye` - End the conversation
- `clear` - Clear conversation history
- `history` - View last 10 messages

## Example Session

```
You: I've been feeling anxious lately
Therapist: [Model generates response...]

You: What can I do about it?
Therapist: [Model generates response...]

You: quit
👋 Goodbye! Take care!
```

## Tips

- The model maintains conversation context (last 10 exchanges)
- First response may take 5-10 seconds (model loading)
- Subsequent responses are faster (~2-5 seconds)
- The model is fine-tuned on therapist conversations, so it responds in a therapeutic style

## Troubleshooting

**"Model not found" error:**
- Make sure training completed successfully
- Check: `modal volume ls training-data`

**Slow responses:**
- First call loads the model (10-20 seconds)
- Subsequent calls are faster
- A10G GPU is used for inference (cost-effective)

**Connection issues:**
- Check Modal dashboard: https://modal.com/apps
- Verify your Modal token: `modal token current`

