"""
Streaming inference endpoint for the fine-tuned therapist model.
Deploy: modal deploy streaming_inference.py
Access: https://your-workspace--therapist-streaming.modal.run

This creates a streaming API endpoint that streams tokens as they're generated.
"""
import modal
import json

# Conditional imports for local parsing vs. Modal execution
if not modal.is_local():
    import torch
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install(
        "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git",
        "transformers",
        "accelerate",
        "bitsandbytes",
        "xformers",
        "torchvision",
        "fastapi[standard]",
    )
)

app = modal.App("therapist-streaming")

training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

# Request model - will be available in Modal's environment
try:
    from pydantic import BaseModel
except ImportError:
    # For local parsing only
    BaseModel = object

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []  # List of {"role": "user/assistant", "content": "..."}
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9

@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/data": training_volume},
    container_idle_timeout=300,  # Keep container alive for 5 minutes
)
class TherapistModel:
    """Modal class to keep model loaded in memory for faster inference"""
    
    @modal.enter()
    def load_model(self):
        """Load the model once when container starts"""
        from unsloth import FastLanguageModel
        
        print("Loading fine-tuned therapist model...")
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name="/data/qwen_therapist_lora",
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(self.model)
        print("✅ Model loaded and ready for streaming inference!")
    
    @modal.method()
    def generate_stream(self, messages: list, max_tokens: int = 512, temperature: float = 0.7, top_p: float = 0.9):
        """Generator that yields tokens as they're generated"""
        import torch
        
        # Format messages for tokenizer
        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to("cuda")
        
        # Generate with streaming using TextIteratorStreamer
        with torch.no_grad():
            from transformers import TextIteratorStreamer
            from threading import Thread
            
            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_prompt=True,
                skip_special_tokens=True
            )
            
            # Start generation in a separate thread
            generation_kwargs = {
                "input_ids": inputs,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": True,
                "streamer": streamer,
                "pad_token_id": self.tokenizer.eos_token_id,
            }
            
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Yield tokens as they come (SSE format)
            for token in streamer:
                if token:
                    yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
            
            # Send completion signal
            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
            thread.join()

@app.function(image=image)
@modal.fastapi_endpoint(method="POST", label="therapist-streaming")
def stream_chat(data: dict):
    """
    Streaming chat endpoint - streams tokens as they're generated.
    
    Example curl:
    curl -X POST https://your-workspace--therapist-streaming.modal.run/stream_chat \\
      -H "Content-Type: application/json" \\
      -d '{"message": "I feel anxious", "max_tokens": 256}'
    """
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, ValidationError
    
    # Parse request data
    try:
        request = ChatRequest(**data)
    except Exception:
        # Fallback if ChatRequest not available
        request = type('obj', (object,), {
            'message': data.get('message', ''),
            'conversation_history': data.get('conversation_history', []),
            'max_tokens': data.get('max_tokens', 512),
            'temperature': data.get('temperature', 0.7),
            'top_p': data.get('top_p', 0.9),
        })()
    
    # Build conversation history
    messages = request.conversation_history.copy() if hasattr(request, 'conversation_history') and request.conversation_history else []
    messages.append({"role": "user", "content": request.message})
    
    # Get model instance and stream
    model_instance = TherapistModel()
    
    # Create streaming response using remote_gen to stream from Modal function
    return StreamingResponse(
        model_instance.generate_stream.remote_gen(
            messages=messages,
            max_tokens=getattr(request, 'max_tokens', 512),
            temperature=getattr(request, 'temperature', 0.7),
            top_p=getattr(request, 'top_p', 0.9),
        ),
        media_type="text/event-stream",
    )

@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def health():
    """Health check endpoint"""
    return {"status": "healthy", "model": "qwen_therapist_lora"}

@app.local_entrypoint()
def main():
    """Test the streaming endpoint locally"""
    print("="*70)
    print("🚀 Streaming Inference Endpoint")
    print("="*70)
    print("\nTo deploy:")
    print("  modal deploy streaming_inference.py")
    print("\nAfter deployment, you'll get a URL like:")
    print("  https://your-workspace--therapist-streaming.modal.run/stream_chat")
    print("\nTest with curl:")
    print("  curl -X POST https://your-workspace--therapist-streaming.modal.run/stream_chat \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"message\": \"I feel anxious\", \"max_tokens\": 256}'")
    print("\nOr test streaming in Python:")
    print("""
import requests
import json

url = "https://your-workspace--therapist-streaming.modal.run/stream_chat"
response = requests.post(
    url,
    json={"message": "I've been feeling stressed", "max_tokens": 256},
    stream=True
)

for line in response.iter_lines():
    if line:
        decoded = line.decode()
        if decoded.startswith("data: "):
            data = json.loads(decoded[6:])  # Remove "data: " prefix
            if not data.get("done"):
                print(data["token"], end="", flush=True)
            else:
                print("\\n[Stream complete]")
""")
