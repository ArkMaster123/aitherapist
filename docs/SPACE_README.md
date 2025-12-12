---
title: Qwen2.5-7B Therapist Chatbot
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: apache-2.0
---

# Qwen2.5-7B Therapist Chatbot

A fine-tuned language model for therapeutic conversations, powered by Modal.ai vLLM for fast inference.

## 🎯 About

This chatbot is a fine-tuned version of **Qwen/Qwen2.5-7B-Instruct**, specifically trained on therapist conversations to provide empathetic, supportive responses.

## 🚀 Features

- **Fast Inference**: Powered by Modal.ai vLLM server
- **Streaming Responses**: Real-time token streaming for better UX
- **Conversation History**: Maintains context throughout the conversation
- **Open Source**: Model and code are publicly available

## 📊 Model Details

- **Base Model**: [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- **Fine-tuning Method**: LoRA (Low-Rank Adaptation)
- **Training Dataset**: [Jyz1331/therapist_conversations](https://huggingface.co/datasets/Jyz1331/therapist_conversations)
- **Training Platform**: Modal.ai with H100 GPUs
- **Training Time**: ~10 minutes

## 🔗 Links

- **Model**: [View on Hugging Face](https://huggingface.co/YOUR_USERNAME/qwen2.5-7b-therapist)
- **Dataset**: [therapist_conversations](https://huggingface.co/datasets/Jyz1331/therapist_conversations)
- **Base Model**: [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)

## ⚠️ Disclaimer

This is a research model and should **not** be used as a replacement for professional mental health services. If you're experiencing a mental health crisis, please contact a licensed professional or emergency services.

## 💻 Usage

### In Python

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("YOUR_USERNAME/qwen2.5-7b-therapist")
tokenizer = AutoTokenizer.from_pretrained("YOUR_USERNAME/qwen2.5-7b-therapist")

messages = [
    {"role": "user", "content": "I'm feeling anxious about work"}
]

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

inputs = tokenizer([text], return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=512)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

### Via API (OpenAI-compatible)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-server-url/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="qwen-therapist",
    messages=[{"role": "user", "content": "I'm feeling anxious"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## 📝 Citation

```bibtex
@misc{qwen2.5-7b-therapist,
  author = {Your Name},
  title = {Qwen2.5-7B-Instruct Therapist},
  year = {2025},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/YOUR_USERNAME/qwen2.5-7b-therapist}}
}
```

## 🙏 Acknowledgments

- Qwen team for the base model
- Jyz1331 for the therapist conversations dataset
- Modal.ai for the inference infrastructure
- Hugging Face for the platform

