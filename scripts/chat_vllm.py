#!/usr/bin/env python3
"""
Local CLI script using OpenAI-compatible API from vLLM server.
Much faster than the previous approach!

Usage: python3 chat_vllm.py "your message"
Or: python3 chat_vllm.py (interactive mode)
"""
import sys
from openai import OpenAI

# Get server URL (update after deploying)
SERVER_URL = None  # Will be set after deployment

def get_client():
    """Get OpenAI client connected to vLLM server"""
    if SERVER_URL is None:
        print("❌ Error: Server URL not set!")
        print("\n1. Deploy the server:")
        print("   modal deploy vllm_server.py")
        print("\n2. Update SERVER_URL in this file with the URL from deployment")
        print("   Or set it as environment variable: export VLLM_SERVER_URL=...")
        sys.exit(1)
    
    return OpenAI(
        base_url=f"{SERVER_URL}/v1",
        api_key="not-needed"  # vLLM doesn't require auth
    )

def chat_once(message: str, history: list = None):
    """Send a single message"""
    client = get_client()
    
    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    response = client.chat.completions.create(
        model="qwen-therapist",
        messages=messages,
        stream=False,
    )
    
    return response.choices[0].message.content

def chat_stream(message: str, history: list = None):
    """Stream response token by token"""
    client = get_client()
    
    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model="qwen-therapist",
            messages=messages,
            stream=True,
            max_tokens=512,
            temperature=0.7,
        )
        
        full_response = ""
        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    content = delta.content
                    print(content, end="", flush=True)
                    full_response += content
        
        # If no content was streamed, check for error
        if not full_response:
            print("[No response received]", end="", flush=True)
        
        print()  # New line after streaming
        return full_response
    
    except Exception as e:
        print(f"\n[Stream Error: {e}]", end="", flush=True)
        raise

def chat_interactive():
    """Interactive chat mode with streaming"""
    import os
    
    # Try to get URL from environment or use default
    global SERVER_URL
    SERVER_URL = os.getenv("VLLM_SERVER_URL", SERVER_URL)
    
    if SERVER_URL is None:
        print("="*70)
        print("❌ Server URL not configured!")
        print("="*70)
        print("\n1. Deploy the server:")
        print("   modal deploy vllm_server.py")
        print("\n2. Set the URL:")
        print("   export VLLM_SERVER_URL=https://your-workspace--vllm-therapist-serve.modal.run")
        print("   OR edit chat_vllm.py and set SERVER_URL")
        print("\n" + "="*70)
        return
    
    print("="*70)
    print("💬 Therapist Chatbot (vLLM - OpenAI Compatible API)")
    print("="*70)
    print(f"\n📡 Server: {SERVER_URL}")
    print("\n💡 Commands:")
    print("  • Type your message and press Enter")
    print("  • Type 'quit', 'exit', or 'bye' to end")
    print("  • Type 'clear' to clear conversation history")
    print("\n⚡ Responses stream in real-time!")
    print("="*70 + "\n")
    
    conversation_history = []
    
    while True:
        try:
            # Flush any pending output before reading input
            sys.stdout.flush()
            sys.stderr.flush()
            
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
            
            # Stream response
            print("Therapist: ", end="", flush=True)
            response = None
            
            try:
                # Try streaming first
                response = chat_stream(user_input, conversation_history)
                
            except Exception as stream_error:
                # Fallback to non-streaming if streaming fails
                print(f"\n[Streaming failed: {stream_error}]")
                print("[Trying non-streaming...]", end="", flush=True)
                try:
                    response = chat_once(user_input, conversation_history)
                    print(f"\r{' '*50}")  # Clear the "trying" message
                    print(response)
                except Exception as non_stream_error:
                    print(f"\n❌ Both streaming and non-streaming failed!")
                    print(f"   Streaming error: {stream_error}")
                    print(f"   Non-streaming error: {non_stream_error}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            if not response or len(response.strip()) == 0:
                print("\n⚠️  Empty response received. Check server status.")
                print(f"   Server URL: {SERVER_URL}")
                continue
            
            # Add to history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response})
            
            # Limit history
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            print()  # Blank line after response
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Take care!\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye! Take care!\n")
            break
        except Exception as e:
            import traceback
            print(f"\n❌ Unexpected error: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}\n")
            # Continue the loop instead of breaking
            continue
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Take care!\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye! Take care!\n")
            break

if __name__ == "__main__":
    import os
    
    # Try to get URL from environment
    SERVER_URL = os.getenv("VLLM_SERVER_URL", SERVER_URL)
    
    if len(sys.argv) > 1:
        # Single message mode
        if SERVER_URL is None:
            print("❌ Error: Set VLLM_SERVER_URL environment variable or edit chat_vllm.py")
            sys.exit(1)
        
        message = " ".join(sys.argv[1:])
        print(f"You: {message}\n")
        print("Therapist: ", end="", flush=True)
        try:
            response = chat_stream(message)
            print()
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
    else:
        # Interactive mode
        chat_interactive()

