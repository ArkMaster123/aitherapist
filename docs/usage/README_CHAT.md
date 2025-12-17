# Local CLI Chat Script

## Quick Start

**Single message:**
```bash
python chat.py "I feel anxious"
```

**Interactive mode:**
```bash
python chat.py
```

## How It Works

- **Local script** (`chat.py`) runs on your machine
- **Calls Modal function** remotely (model runs on Modal GPU)
- **Model stays loaded** in Modal container (fast responses!)
- **No interactive Modal session** - just clean CLI calls

## Usage Examples

**Single message:**
```bash
$ python chat.py "How do I deal with stress?"
You: How do I deal with stress?

🤔 Thinking...
Therapist: [Response from Modal...]
```

**Interactive chat:**
```bash
$ python chat.py
💬 Therapist Chatbot (Local CLI → Modal GPU)
======================================================================

You: I've been feeling anxious
Therapist: [Response...]

You: What can I do?
Therapist: [Response...]

You: quit
👋 Goodbye!
```

## Benefits

✅ **Runs locally** - No Modal interactive session  
✅ **Fast** - Model stays loaded in Modal container  
✅ **Simple** - Just `python chat.py`  
✅ **Flexible** - Single message or interactive mode  

## Make it executable (optional)

```bash
chmod +x chat.py
./chat.py "your message"
```

