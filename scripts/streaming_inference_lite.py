"""
Lightweight streaming inference - NO training dependencies!
Just loads the LoRA adapter using transformers + peft (no Unsloth needed).
Deploy: modal deploy streaming_inference_lite.py
"""
import modal
import json

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "transformers>=4.40.0",  # For model loading
        "peft",  # For LoRA adapter loading
        "accelerate",  # For model loading
        "bitsandbytes",  # For 4-bit quantization
        "torch",  # PyTorch
        "fastapi[standard]",  # For API
        "sentencepiece",  # For tokenizer
    )
)

app = modal.App("therapist-streaming-lite")

training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

# Request model
try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = object

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9

@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/data": training_volume},
    container_idle_timeout=300,
)
class TherapistModel:
    """Lightweight model class - uses transformers + peft (no Unsloth!)"""
    
    @modal.enter()
    def load_model(self):
        """Load base model + LoRA adapter using transformers + peft"""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        import torch
        
        print("Loading base model (Qwen2.5-7B-Instruct)...")
        base_model_name = "Qwen/Qwen2.5-7B-Instruct"
        
        # Load base model with 4-bit quantization
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_4bit=True,
            trust_remote_code=True,
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            trust_remote_code=True,
        )
        
        # Load LoRA adapter from Modal volume
        lora_path = "/data/qwen_therapist_lora"
        print(f"Loading LoRA adapter from {lora_path}...")
        self.model = PeftModel.from_pretrained(self.model, lora_path)
        
        # Merge LoRA weights for faster inference (optional)
        # self.model = self.model.merge_and_unload()
        
        self.model.eval()  # Set to eval mode
        print("✅ Model loaded (lightweight - no Unsloth needed!)")
    
    @modal.method()
    def generate_stream(self, messages: list, max_tokens: int = 512, temperature: float = 0.7, top_p: float = 0.9):
        """Generator that yields tokens as they're generated"""
        import torch
        from transformers import TextIteratorStreamer
        from threading import Thread
        
        # Format messages for tokenizer
        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(self.model.device)
        
        # Generate with streaming
        with torch.no_grad():
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
@modal.fastapi_endpoint(method="POST", label="therapist-streaming-lite")
def stream_chat(data: dict):
    """Lightweight streaming endpoint"""
    from fastapi.responses import StreamingResponse
    
    # Parse request
    try:
        request = ChatRequest(**data)
    except Exception:
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
    """Health check"""
    return {"status": "healthy", "model": "qwen_therapist_lora", "mode": "lite"}

@app.local_entrypoint()
def main():
    print("="*70)
    print("🚀 Lightweight Streaming Inference (No Unsloth!)")
    print("="*70)
    print("\nDeploy:")
    print("  modal deploy streaming_inference_lite.py")
    print("\nThis version:")
    print("  ✅ Uses transformers + peft (standard libraries)")
    print("  ✅ No Unsloth dependency")
    print("  ✅ No training libraries (trl, datasets, etc.)")
    print("  ✅ Faster image build")
    print("  ✅ Smaller image size")
    print("\n" + "="*70)

