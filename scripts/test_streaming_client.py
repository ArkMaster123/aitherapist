"""
Test client for the streaming inference endpoint.
Run: python test_streaming_client.py

Make sure to deploy first: modal deploy streaming_inference.py
"""
import requests
import json
import sys

def test_streaming(url: str, message: str, max_tokens: int = 256):
    """Test the streaming endpoint"""
    print("="*70)
    print("🧪 Testing Streaming Endpoint")
    print("="*70)
    print(f"\nURL: {url}")
    print(f"Message: {message}")
    print(f"Max tokens: {max_tokens}")
    print("\n" + "="*70)
    print("Streaming response:\n")
    
    try:
        response = requests.post(
            url,
            json={
                "message": message,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            stream=True,
            timeout=60,
        )
        
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                decoded = line.decode()
                if decoded.startswith("data: "):
                    try:
                        data = json.loads(decoded[6:])  # Remove "data: " prefix
                        if not data.get("done"):
                            token = data.get("token", "")
                            print(token, end="", flush=True)
                            full_response += token
                        else:
                            print("\n\n" + "="*70)
                            print("✅ Stream complete!")
                            print("="*70)
                            print(f"\nFull response ({len(full_response)} chars):")
                            print(full_response)
                            return full_response
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️  JSON decode error: {e}")
                        print(f"Raw line: {decoded}")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

if __name__ == "__main__":
    # Get URL from command line or use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("⚠️  No URL provided!")
        print("\nUsage: python test_streaming_client.py <endpoint_url>")
        print("\nExample:")
        print("  python test_streaming_client.py https://your-workspace--therapist-streaming.modal.run/stream_chat")
        print("\nOr set URL in the script and run:")
        print("  python test_streaming_client.py")
        sys.exit(1)
    
    # Test messages
    test_messages = [
        "I've been feeling really anxious lately. Can you help me understand what might be causing this?",
        "How do I deal with stress at work?",
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n\n{'='*70}")
        print(f"Test {i}/{len(test_messages)}")
        print(f"{'='*70}\n")
        test_streaming(url, message, max_tokens=256)
        
        if i < len(test_messages):
            input("\nPress Enter to continue to next test...")

