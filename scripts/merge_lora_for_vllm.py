"""
Merge LoRA adapter into base model for vLLM serving.
Run this ONCE to create a merged model that vLLM can serve directly.

Run: modal run merge_lora_for_vllm.py
"""
import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "transformers>=4.40.0",
        "peft",
        "accelerate",
        "torch",
        "sentencepiece",
    )
)

app = modal.App("merge-lora")

training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
LORA_PATH = "/data/qwen_therapist_lora_safety"  # Use safety-trained model
MERGED_PATH = "/data/qwen_therapist_merged_safety"  # New merged model path

@app.function(
    image=image,
    gpu="A10G",
    volumes={"/data": training_volume},
    timeout=1800,  # 30 minutes
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
def merge_lora():
    """Merge LoRA adapter into base model for vLLM"""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch
    from pathlib import Path
    
    print("="*70)
    print("Merging Safety-Trained LoRA Adapter for vLLM")
    print("="*70)
    
    print(f"\n[1/4] Loading base model: {MODEL_NAME}")
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    print("✅ Base model loaded")
    
    print(f"\n[2/4] Loading LoRA adapter from {LORA_PATH}")
    model = PeftModel.from_pretrained(base_model, LORA_PATH)
    print("✅ LoRA adapter loaded")
    
    print(f"\n[3/4] Merging LoRA weights into base model...")
    merged_model = model.merge_and_unload()
    print("✅ LoRA merged")
    
    print(f"\n[4/4] Saving merged model to {MERGED_PATH}...")
    Path(MERGED_PATH).mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(MERGED_PATH)
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.save_pretrained(MERGED_PATH)
    
    print("✅ Merged model saved!")
    print(f"\n📦 Merged model location: {MERGED_PATH}")
    print("🚀 Ready for vLLM serving!")
    print("="*70)

@app.local_entrypoint()
def main():
    print("Merging LoRA adapter for vLLM...")
    merge_lora.remote()
    print("\n✅ Done! You can now deploy vllm_server.py")

