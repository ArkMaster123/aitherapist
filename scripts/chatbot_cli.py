"""
Interactive CLI chatbot using the fine-tuned therapist model.
Run: modal run chatbot_cli.py

This creates an interactive chat interface to test your fine-tuned model.
"""
import modal

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
    )
)

app = modal.App("therapist-chatbot")

training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

# Global variable to store conversation history
conversation_history = []

@app.function(
    image=image,
    gpu="A10G",  # A10G is fine for inference
    volumes={"/data": training_volume},
    timeout=300,  # 5 minutes per request
)
def get_response(user_message: str, history: list = None):
    """Get a response from the fine-tuned model"""
    from unsloth import FastLanguageModel
    import torch
    
    # Load model (will be cached after first call)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="/data/qwen_therapist_lora",
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    
    FastLanguageModel.for_inference(model)
    
    # Use provided history or empty list
    if history is None:
        history = []
    
    # Add user message
    messages = history + [{"role": "user", "content": user_message}]
    
    # Tokenize
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to("cuda")
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    # Decode
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract assistant response
    # Find the assistant's part
    if "assistant" in full_response.lower():
        parts = full_response.split("assistant")
        assistant_response = parts[-1].strip()
    else:
        # Try to extract the new part
        user_text = tokenizer.decode(inputs[0], skip_special_tokens=True)
        if user_text in full_response:
            assistant_response = full_response.replace(user_text, "").strip()
        else:
            assistant_response = full_response[-500:].strip()
    
    # Clean up
    assistant_response = assistant_response.replace("<|im_start|>", "").replace("<|im_end|>", "").strip()
    
    return assistant_response

@app.local_entrypoint()
def main():
    """Interactive CLI chatbot - runs locally, calls Modal for inference"""
    print("="*70)
    print("🧠 Therapist Chatbot - Loading Model...")
    print("="*70)
    print("\n⏳ Initializing model on Modal (first call may take a moment)...\n")
    
    # Test connection with a simple message
    try:
        test_response = get_response.remote("Hello, I'm testing the connection.")
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
    print("\n" + "="*70 + "\n")
    
    conversation_history = []
    
    while True:
        try:
            # Get user input
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Goodbye! Take care!\n")
                break
            
            if not user_input:
                print("💡 Please type a message, or 'quit' to exit.\n")
                continue
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\n👋 Goodbye! Take care!\n")
                break
            
            # Check for clear command
            if user_input.lower() == 'clear':
                conversation_history = []
                print("\n🧹 Conversation history cleared!\n")
                continue
            
            # Check for history command
            if user_input.lower() == 'history':
                print("\n📜 Conversation History:")
                for i, msg in enumerate(conversation_history[-10:], 1):  # Show last 10
                    role = "You" if msg["role"] == "user" else "Therapist"
                    content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    print(f"  {i}. {role}: {content}")
                print()
                continue
            
            # Get response from Modal
            print("🤔 Thinking...", end="", flush=True)
            try:
                response = get_response.remote(user_input, conversation_history)
                print(f"\r{' '*50}")  # Clear "Thinking..." message
                print(f"Therapist: {response}\n")
                
                # Add to history
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": response})
                
                # Limit history to last 10 exchanges (20 messages)
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
