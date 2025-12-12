"""
Hugging Face Space for Qwen2.5-7B Therapist Chatbot
Connects to Modal vLLM server for fast inference
"""
import gradio as gr
import os
from openai import OpenAI

# Get server URL from environment or use default
VLLM_SERVER_URL = os.getenv("VLLM_SERVER_URL", "https://whataidea--vllm-therapist-serve.modal.run")

# Initialize OpenAI client
client = OpenAI(
    base_url=f"{VLLM_SERVER_URL}/v1",
    api_key="not-needed"
)

def chat(message, history):
    """Chat function for Gradio"""
    # Convert Gradio history format to OpenAI format
    messages = []
    if history:
        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    try:
        # Get streaming response
        response = client.chat.completions.create(
            model="qwen-therapist",
            messages=messages,
            stream=True,
            max_tokens=512,
            temperature=0.7,
        )
        
        # Stream the response
        full_response = ""
        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    content = delta.content
                    full_response += content
                    yield full_response
    
    except Exception as e:
        yield f"❌ Error: {str(e)}\n\nPlease check that the vLLM server is running at:\n{VLLM_SERVER_URL}"

# Create Gradio interface
with gr.Blocks(
    title="Qwen2.5-7B Therapist Chatbot",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown("""
    # 🧠 Qwen2.5-7B Therapist Chatbot
    
    A fine-tuned language model trained for therapeutic conversations.
    
    **Model**: Fine-tuned Qwen/Qwen2.5-7B-Instruct on therapist conversations dataset
    
    **Powered by**: [Modal.ai](https://modal.com) vLLM server for fast inference
    
    ⚠️ **Disclaimer**: This is a research model and should not be used as a replacement for professional mental health services.
    """)
    
    chatbot = gr.Chatbot(
        label="Conversation",
        height=500,
        show_copy_button=True,
    )
    
    with gr.Row():
        msg = gr.Textbox(
            label="Your Message",
            placeholder="Type your message here...",
            scale=4,
            container=False,
        )
        submit_btn = gr.Button("Send", variant="primary", scale=1)
        clear_btn = gr.Button("Clear", scale=1)
    
    gr.Markdown("""
    ### 💡 Tips:
    - Be specific about your feelings and concerns
    - The model is trained to provide supportive, empathetic responses
    - Type "clear" or click "Clear" to start a new conversation
    
    ### 🔗 Links:
    - [Model on Hugging Face](https://huggingface.co/YOUR_USERNAME/qwen2.5-7b-therapist)
    - [Training Dataset](https://huggingface.co/datasets/Jyz1331/therapist_conversations)
    - [Base Model](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
    """)
    
    # Event handlers
    msg.submit(chat, [msg, chatbot], [chatbot]).then(
        lambda: "", None, [msg]
    )
    submit_btn.click(chat, [msg, chatbot], [chatbot]).then(
        lambda: "", None, [msg]
    )
    clear_btn.click(lambda: None, None, [chatbot])

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )

