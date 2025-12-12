#!/usr/bin/env python3
"""
Local CLI script to chat with the Modal-hosted therapist model.
Usage: python3 chat.py "your message"
Or: python3 chat.py (interactive mode)
"""
import sys
import subprocess
import json

def chat_once(message: str):
    """Send a single message via Modal CLI"""
    # Use modal run with the function directly
    cmd = [
        "python3", "-c", f"""
import modal
from chatbot_cli_fast import app, TherapistModel

with app.run():
    model = TherapistModel()
    response = model.get_response.remote('{message.replace("'", "\\'")}')
    print(response)
"""
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="/Users/noahsark/Documents/vibecoding/finetuningtest")
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        return f"Error: {result.stderr}"

def chat_interactive():
    """Interactive chat mode - keeps connection open!"""
    print("="*70)
    print("💬 Therapist Chatbot (Local CLI → Modal GPU)")
    print("="*70)
    print("\n💡 Commands:")
    print("  • Type your message and press Enter")
    print("  • Type 'quit', 'exit', or 'bye' to end")
    print("  • Type 'clear' to clear conversation history")
    print("\n⏳ Connecting to Modal (this happens once)...")
    print("="*70 + "\n")
    
    # Import and connect ONCE - keep connection open
    import modal
    from chatbot_cli_fast import app, TherapistModel
    
    # Keep app connection open for entire session - model stays loaded!
    with app.run():
        print("🤔 Loading model (first time only, ~30-60 seconds)...", end="", flush=True)
        # Create model instance ONCE - this triggers @modal.enter() to load model
        # All subsequent calls to model.get_response.remote() will reuse THIS SAME container!
        model = TherapistModel()
        print(f"\r{' '*50}")
        print("✅ Connected! Model loaded and ready.\n")
        print("⚡ Model stays loaded in Modal container - all responses will be fast!\n")
        print("💡 Same container reused for all messages (no reloading!)\n")
        print("="*70 + "\n")
        
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
                
                # Call Modal function - reuses SAME model instance & SAME container!
                print("🤔 Thinking...", end="", flush=True)
                try:
                    # This reuses the SAME model instance - Modal keeps container alive!
                    # All calls to model.get_response.remote() use the same container
                    response = model.get_response.remote(user_input, conversation_history)
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
                    print(f"❌ Error: {e}\n")
                    import traceback
                    traceback.print_exc()
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Take care!\n")
                break
            except EOFError:
                print("\n\n👋 Goodbye! Take care!\n")
                break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single message mode
        message = " ".join(sys.argv[1:])
        print(f"You: {message}\n")
        print("🤔 Thinking...", end="", flush=True)
        try:
            import modal
            from chatbot_cli_fast import app, TherapistModel
            
            # Connect once, use model, then close
            with app.run():
                model = TherapistModel()  # Loads model once
                response = model.get_response.remote(message)
            
            print(f"\r{' '*50}")
            print(f"Therapist: {response}\n")
        except Exception as e:
            print(f"\r{' '*50}")
            print(f"❌ Error: {e}\n")
    else:
        # Interactive mode - keeps connection open!
        chat_interactive()
