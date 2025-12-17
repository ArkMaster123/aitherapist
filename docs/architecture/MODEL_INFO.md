# Model Information

## Model Used
**Qwen/Qwen2.5-7B-Instruct**

- **Type**: Causal Language Models
- **Parameters**: 7.61B (6.53B non-embedding)
- **Layers**: 28
- **Context Length**: Up to 131,072 tokens
- **Generation Length**: Up to 8,192 tokens
- **Architecture**: Transformers with RoPE, SwiGLU, RMSNorm

## Hugging Face Card
https://huggingface.co/Qwen/Qwen2.5-7B-Instruct

## Quickstart (from model card)
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen2.5-7B-Instruct"

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
```

## Our Fine-Tuned Version
- **Base Model**: Qwen/Qwen2.5-7B-Instruct
- **LoRA Adapter**: Saved to `/data/qwen_therapist_lora` on Modal volume
- **Dataset**: Jyz1331/therapist_conversations
- **Training**: LoRA fine-tuning with Unsloth

## Loading Fine-Tuned Model
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-7B-Instruct",
    torch_dtype="auto",
    device_map="auto",
    load_in_4bit=True,
)

# Load LoRA adapter
model = PeftModel.from_pretrained(model, "/data/qwen_therapist_lora")
```

