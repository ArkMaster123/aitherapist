"""
FAST CLI chatbot - Model stays loaded in memory!
Uses @app.cls with @modal.enter() to load model once, keep container alive.
Run: modal run chatbot_cli_fast.py
"""
import modal

# Lightweight image - no Unsloth, no training dependencies!
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "transformers>=4.40.0",
        "peft",
        "accelerate",
        "bitsandbytes",
        "torch",
        "sentencepiece",
    )
)

app = modal.App("therapist-chatbot-fast")

training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/data": training_volume},
    scaledown_window=300,  # Keep container alive for 5 minutes
    timeout=600,
)
class TherapistModel:
    """Model class - loads once, stays in memory for fast inference!"""
    
    @modal.enter()
    def load_model(self):
        """Load model ONCE when container starts - not on every call!"""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        import torch
        
        print("="*70)
        print("Loading model (this happens ONCE per container)...")
        print("="*70)
        
        base_model_name = "Qwen/Qwen2.5-7B-Instruct"
        lora_path = "/data/qwen_therapist_lora"
        
        print(f"Loading base model: {base_model_name}")
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype="auto",  # Use auto dtype as recommended in model card
            device_map="auto",
            load_in_4bit=True,
            trust_remote_code=True,
        )
        
        print("Loading tokenizer...")
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            trust_remote_code=True,
        )
        
        print(f"Loading LoRA adapter from {lora_path}...")
        # Load LoRA adapter
        self.model = PeftModel.from_pretrained(self.model, lora_path)
        self.model.eval()
        
        print("✅ Model loaded and ready! (Container will stay alive for fast responses)")
        print("="*70)
    
    @modal.method()
    def get_response(self, user_message: str, history: list = None):
        """Get response - model is already loaded, super fast! Follows model card exactly."""
        import torch
        
        # Use provided history or empty list
        if history is None:
            history = []
        
        # Add user message
        messages = history + [{"role": "user", "content": user_message}]
        
        # Follow model card pattern exactly:
        # 1. Apply chat template (tokenize=False first)
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # 2. Tokenize separately
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        
        # 3. Generate
        with torch.no_grad():
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
            )
        
        # 4. Extract only new tokens (as per model card)
        generated_ids = [
            output_ids[len(input_ids):] 
            for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        # 5. Decode only the new tokens
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return response

@app.local_entrypoint()
def main():
    """Interactive CLI chatbot - model stays loaded for fast responses!"""
    print("="*70)
    print("🚀 FAST Therapist Chatbot")
    print("="*70)
    print("\n⚡ Model loads ONCE, stays in memory!")
    print("⚡ Container stays alive for 5 minutes")
    print("⚡ Subsequent responses are INSTANT!")
    print("\n⏳ Initializing model on Modal (first call loads model)...\n")
    
    # Create model instance (this triggers @modal.enter() to load model)
    model_instance = TherapistModel()
    
    # Test connection
    try:
        test_response = model_instance.get_response.remote("Hello, I'm testing the connection.")
        print("✅ Model loaded and ready!\n")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return
    
    print("="*70)
    print("💬 Therapist Chatbot - Ready to Chat!")
    print("="*70)
    print("\n💡 Commands:")
    print("  • Type your message and press Enter")
    print("  • Type 'quit', 'exit', or 'bye' to end")
    print("  • Type 'clear' to clear conversation history")
    print("  • Type 'history' to see conversation history")
    print("\n⚡ First response may take 2-3 seconds (model already loaded!)")
    print("⚡ Subsequent responses are INSTANT!")
    print("\n" + "="*70 + "\n")
    
    conversation_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                print("💡 Please type a message, or 'quit' to exit.\n")
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n👋 Goodbye! Take care!\n")
                break
            
            if user_input.lower() == 'clear':
                conversation_history = []
                print("\n🧹 Conversation history cleared!\n")
                continue
            
            if user_input.lower() == 'history':
                print("\n📜 Conversation History:")
                for i, msg in enumerate(conversation_history[-10:], 1):
                    role = "You" if msg["role"] == "user" else "Therapist"
                    content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    print(f"  {i}. {role}: {content}")
                print()
                continue
            
            # Get response from Modal (model already loaded - FAST!)
            print("🤔 Thinking...", end="", flush=True)
            try:
                response = model_instance.get_response.remote(user_input, conversation_history)
                print(f"\r{' '*50}")
                print(f"Therapist: {response}\n")
                
                # Add to history
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": response})
                
                # Limit history
                if len(conversation_history) > 20:
                    conversation_history = conversation_history[-20:]
            
            except Exception as e:
                print(f"\r{' '*50}")
                print(f"❌ Error: {e}")
                print("Please try again.\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Take care!\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye! Take care!\n")
            break

