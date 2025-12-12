#!/usr/bin/env python3
"""
Upload your fine-tuned therapist model to Hugging Face Hub!
This will make it public and shareable.

Usage:
1. Set your Hugging Face token: export HF_TOKEN=your_token_here
2. Run: modal run upload_model_to_hf.py
"""
import modal
import os

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "huggingface_hub",
        "transformers",
        "peft",
        "accelerate",
    )
)

app = modal.App("upload-model-to-hf")
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

@app.function(
    image=image,
    volumes={"/data": training_volume},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=3600,  # 1 hour for large uploads
)
def upload_model():
    """Upload merged model to Hugging Face Hub"""
    from huggingface_hub import HfApi, login
    from pathlib import Path
    import os
    
    # Get HF token from secret
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("❌ Error: HF_TOKEN not found in secrets!")
        print("   Make sure you have a 'huggingface-secret' Modal secret with HF_TOKEN")
        return
    
    # Login to HF
    login(token=hf_token)
    
    # Model paths - use safety-trained version
    merged_model_path = "/data/qwen_therapist_merged_safety"
    lora_path = "/data/qwen_therapist_lora_safety"
    
    # Check if merged model exists
    if not os.path.exists(merged_model_path):
        print("⚠️  Merged model not found. Checking for LoRA adapter...")
        if os.path.exists(lora_path):
            print("   Found LoRA adapter. Merging now...")
            # Merge LoRA with base model
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel
            import torch
            
            base_model_name = "Qwen/Qwen2.5-7B-Instruct"
            
            print("   Loading base model...")
            model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )
            
            print("   Loading LoRA adapter...")
            model = PeftModel.from_pretrained(model, lora_path)
            
            print("   Merging LoRA weights...")
            model = model.merge_and_unload()
            
            print(f"   Saving merged model to {merged_model_path}...")
            os.makedirs(merged_model_path, exist_ok=True)
            model.save_pretrained(merged_model_path)
            tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
            tokenizer.save_pretrained(merged_model_path)
            print("   ✅ Merged model created!")
        else:
            print("❌ Error: Neither merged model nor LoRA adapter found!")
            print(f"   Checked: {merged_model_path}")
            print(f"   Checked: {lora_path}")
            return
    
    # Get your HF username
    api = HfApi(token=hf_token)
    user_info = api.whoami()
    username = user_info["name"]
    
    # Model repository name (you can change this!)
    repo_id = f"{username}/qwen2.5-7b-therapist"
    
    print("="*70)
    print("🚀 Uploading Model to Hugging Face Hub")
    print("="*70)
    print(f"\n📦 Repository: {repo_id}")
    print(f"📁 Source: {merged_model_path}")
    print(f"👤 Username: {username}")
    print("\n⏳ This may take a while (model is ~14GB)...")
    print("="*70 + "\n")
    
    # Create repository if it doesn't exist
    print("📝 Checking/Creating repository...")
    try:
        # Try to get repo info first to see if it exists
        try:
            repo_info = api.repo_info(repo_id=repo_id, repo_type="model")
            print(f"✅ Repository already exists: {repo_id}")
        except Exception:
            # Repository doesn't exist, create it
            print(f"📦 Creating new repository: {repo_id}")
            api.create_repo(
                repo_id=repo_id,
                repo_type="model",
                exist_ok=False,  # We know it doesn't exist
                private=False,  # Make it public
            )
            print("✅ Repository created!")
    except Exception as e:
        print(f"⚠️  Repository check/creation: {e}")
        # Try to create anyway with exist_ok=True
        try:
            api.create_repo(
                repo_id=repo_id,
                repo_type="model",
                exist_ok=True,
                private=False,
            )
            print("✅ Repository ready!")
        except Exception as e2:
            print(f"❌ Failed to create repository: {e2}")
            raise
    
    print("\n📤 Uploading model files...")
    print("   ⏳ This may take 15-30 minutes depending on your connection...")
    print("   📊 Progress will be shown below...\n")
    
    # Upload model
    try:
        api.upload_folder(
            folder_path=merged_model_path,
            repo_id=repo_id,
            repo_type="model",
            commit_message="Update: Safety-trained version with improved crisis handling and response quality",
        )
        print("\n✅ Model files uploaded successfully!")
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        raise
    
    # Create model card
    model_card = f"""---
license: apache-2.0
base_model: Qwen/Qwen2.5-7B-Instruct
tags:
- fine-tuned
- therapy
- counseling
- mental-health
- qwen
- lora
---

# Qwen2.5-7B-Instruct Therapist

This is a fine-tuned version of Qwen/Qwen2.5-7B-Instruct, specifically trained for therapeutic conversations.

## Model Details

- **Base Model**: Qwen/Qwen2.5-7B-Instruct
- **Fine-tuning Method**: LoRA (Low-Rank Adaptation)
- **Training Dataset**: Jyz1331/therapist_conversations + Safety-focused examples
- **Training**: Fine-tuned on Modal.ai with H100 GPUs
- **Version**: Safety-trained (v2) - Improved crisis handling, response quality, and safety

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("{repo_id}")
tokenizer = AutoTokenizer.from_pretrained("{repo_id}")

messages = [
    {{"role": "user", "content": "I'm feeling anxious about work"}}
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

## Training Details

- **GPU**: H100 (80GB VRAM)
- **Training Time**: ~10 minutes (initial) + ~20 minutes (safety training)
- **LoRA Rank**: 16
- **Learning Rate**: 2e-4 (initial), 1e-4 (safety fine-tuning)
- **Batch Size**: 8 (per device) × 2 (gradient accumulation)
- **Safety Improvements**: 3/4 safety tests passing (crisis handling, medical advice, harmful reinforcement)

## Limitations

This model is fine-tuned for therapeutic conversations and should not be used as a replacement for professional mental health services.

## Citation

```bibtex
@misc{{qwen2.5-7b-therapist,
  author = {{Your Name}},
  title = {{Qwen2.5-7B-Instruct Therapist}},
  year = {{2025}},
  publisher = {{Hugging Face}},
  howpublished = {{\\url{{https://huggingface.co/{repo_id}}}}}
}}
```
"""
    
    # Upload model card
    print("\n📝 Uploading model card (README.md)...")
    try:
        api.upload_file(
            path_or_fileobj=model_card.encode(),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="model",
            commit_message="Add model card",
        )
        print("✅ Model card uploaded!")
    except Exception as e:
        print(f"⚠️  Model card upload failed: {e}")
        print("   (You can manually add a README.md later on Hugging Face)")
    
    print("\n" + "="*70)
    print("🎉 Model Uploaded Successfully!")
    print("="*70)
    print(f"\n🌐 View your model:")
    print(f"   https://huggingface.co/{repo_id}")
    print(f"\n📥 Download with:")
    print(f"   from transformers import AutoModelForCausalLM")
    print(f"   model = AutoModelForCausalLM.from_pretrained('{repo_id}')")
    print("\n" + "="*70)

@app.local_entrypoint()
def main():
    print("="*70)
    print("🚀 Uploading Fine-tuned Model to Hugging Face")
    print("="*70)
    print("\n📋 Requirements:")
    print("   1. Hugging Face token in Modal secret 'huggingface-secret'")
    print("   2. Merged model at /data/qwen_therapist_merged (or LoRA at /data/qwen_therapist_lora)")
    print("\n⏳ Starting upload...")
    print("="*70 + "\n")
    
    upload_model.remote()

