#!/usr/bin/env python3
"""
Continue training the fine-tuned therapist model with safety-focused examples.
This adds safety training to address the evaluation failures.

Usage: modal run continue_training_with_safety.py
"""
import modal
import os
import json
from pathlib import Path

# Conditional imports for local parsing vs. Modal execution
if not modal.is_local():
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_dataset, Dataset
    import torch
    from transformers import TrainerCallback

# All packages install automatically in Modal's cloud
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install(
        "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git",
        "transformers",
        "datasets",
        "trl",
        "peft",
        "accelerate",
        "bitsandbytes",
        "xformers",
        "huggingface_hub",
        "torchvision",
        "tensorboard",
        "tqdm",
    )
)

app = modal.App("qwen-therapist-safety-training")

# Persistent volume - your model stays here!
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

@app.function(
    image=image,
    gpu="H100",  # H100 for fast training
    timeout=1800,  # 30 minutes max
    secrets=[modal.Secret.from_name("huggingface-secret")],
    volumes={"/data": training_volume},
)
def continue_training_with_safety():
    """Continue training with safety-focused examples"""
    # Imports inside function
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_dataset, Dataset
    import torch
    from transformers import TrainerCallback
    
    print("="*70)
    print("🛡️  Safety-Focused Training - Continuing from Existing Model")
    print("="*70)
    
    # Load existing fine-tuned model
    print("\n[1/7] Loading existing fine-tuned model...")
    base_model_name = "Qwen/Qwen2.5-7B-Instruct"
    existing_lora_path = "/data/qwen_therapist_lora"
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model_name,
        max_seq_length=2048,
        dtype=torch.bfloat16,
        load_in_4bit=False,  # H100 has enough VRAM
    )
    
    # Load existing LoRA adapter
    print(f"Loading existing LoRA adapter from {existing_lora_path}...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing=False,
        random_state=3407,
    )
    
    # Load existing adapter weights
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, existing_lora_path)
    print("✅ Existing model loaded")
    
    # Load original dataset
    print("\n[2/7] Loading original therapist conversations dataset...")
    dataset_cache_dir = Path("/data/datasets_cache")
    dataset_cache_dir.mkdir(parents=True, exist_ok=True)
    
    original_dataset = load_dataset(
        "Jyz1331/therapist_conversations",
        cache_dir=str(dataset_cache_dir)
    )
    split_name = "train" if "train" in original_dataset else list(original_dataset.keys())[0]
    original_train = original_dataset[split_name]
    print(f"✅ Original dataset: {len(original_train)} examples")
    
    # Load safety dataset from volume (should be uploaded first)
    print("\n[3/7] Loading safety training dataset...")
    
    # Try multiple possible paths
    safety_paths = [
        "/data/safety_training_dataset.json",
        "/data/data/safety_training_dataset.json",  # Sometimes files end up in /data/data/
    ]
    
    safety_path = None
    for path in safety_paths:
        if os.path.exists(path):
            safety_path = path
            break
    
    if safety_path is None:
        print(f"❌ Error: Safety dataset not found at any of: {safety_paths}")
        print("   Listing /data directory contents:")
        if os.path.exists("/data"):
            for item in os.listdir("/data"):
                item_path = os.path.join("/data", item)
                if os.path.isdir(item_path):
                    print(f"   📁 {item}/")
                else:
                    print(f"   📄 {item}")
        print("\n   Please run: modal run upload_safety_dataset.py first")
        return
    
    print(f"   ✅ Found safety dataset at: {safety_path}")
    print(f"   Loading from volume...")
    with open(safety_path, 'r') as f:
        safety_data = json.load(f)
    
    # Create dataset from JSON
    safety_dataset = Dataset.from_list(safety_data)
    print(f"✅ Safety dataset loaded: {len(safety_dataset)} examples")
    
    # Save to volume for future reference
    safety_save_path = "/data/safety_training_dataset.json"
    with open(safety_save_path, 'w') as f:
        json.dump(safety_data, f, indent=2)
    print(f"✅ Safety dataset saved to volume: {safety_save_path}")
    
    # Combine datasets
    print("\n[4/7] Combining datasets...")
    # Convert safety dataset to same format
    def format_safety_dataset(examples):
        """Format safety dataset to match original format"""
        texts = []
        for question, response in zip(examples["question"], examples["response"]):
            text = tokenizer.apply_chat_template(
                [{"role": "user", "content": question},
                 {"role": "assistant", "content": response}],
                tokenize=False,
                add_generation_prompt=False,
            )
            texts.append(text)
        return {"text": texts}
    
    safety_formatted = safety_dataset.map(
        format_safety_dataset,
        batched=True,
        remove_columns=safety_dataset.column_names,
    )
    
    # Format original dataset
    def formatting_prompts_func(examples):
        texts = []
        if "question" in examples and "response" in examples:
            for question, response in zip(examples["question"], examples["response"]):
                text = tokenizer.apply_chat_template(
                    [{"role": "user", "content": question},
                     {"role": "assistant", "content": response}],
                    tokenize=False,
                    add_generation_prompt=False,
                )
                texts.append(text)
        else:
            available_keys = list(examples.keys())
            raise ValueError(f"Unknown dataset format. Available keys: {available_keys}")
        return {"text": texts}
    
    original_formatted = original_train.map(
        formatting_prompts_func,
        batched=True,
        num_proc=os.cpu_count(),
        remove_columns=original_train.column_names,
    )
    
    # Combine: Use all safety examples + sample of original (to balance)
    # Prioritize safety examples by including them all
    combined_dataset = safety_formatted
    
    # Add original dataset (you can adjust the ratio)
    # For now, let's use all original + all safety
    from datasets import concatenate_datasets
    combined_dataset = concatenate_datasets([original_formatted, safety_formatted])
    
    print(f"✅ Combined dataset: {len(combined_dataset)} examples")
    print(f"   - Original: {len(original_formatted)} examples")
    print(f"   - Safety: {len(safety_formatted)} examples")
    
    # Training arguments - continue training with lower learning rate
    print("\n[5/7] Setting up training...")
    print("\n" + "="*70)
    print("📊 TRAINING CONFIGURATION:")
    print("======================================================================")
    print("  • Continuing from existing LoRA adapter")
    print("  • Adding safety-focused examples")
    print("  • Lower learning rate for fine-tuning (1e-4)")
    print("  • Focused on safety improvements")
    print("======================================================================")
    
    # Setup TensorBoard logging
    tensorboard_log_dir = Path("/data/tensorboard_logs_safety")
    tensorboard_log_dir.mkdir(parents=True, exist_ok=True)
    
    class CustomPrinterCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs is not None and "loss" in logs:
                print(f"📈 Step {state.global_step}/{state.max_steps}: Loss = {logs['loss']:.4f}")
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=combined_dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=8,
            gradient_accumulation_steps=2,
            warmup_steps=5,
            num_train_epochs=1,  # 1 epoch should be enough for safety fine-tuning
            learning_rate=1e-4,  # Lower LR for fine-tuning existing model
            fp16=False,
            bf16=True,
            logging_steps=1,
            optim="adamw_torch",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir="/data/outputs_safety",
            save_steps=50,
            report_to="tensorboard",
            dataloader_num_workers=4,
            dataloader_pin_memory=True,
        ),
        callbacks=[CustomPrinterCallback()],
    )
    
    # Train
    print("\n[6/7] Starting safety-focused training...")
    trainer.train()
    print("✅ Training completed")
    
    # Save updated model
    print("\n[7/7] Saving updated model...")
    model_save_path = "/data/qwen_therapist_lora_safety"
    model.save_pretrained(model_save_path)
    tokenizer.save_pretrained(model_save_path)
    print(f"✅ Model saved to {model_save_path}")
    
    # Safety dataset already saved to volume earlier
    
    # Optimize for inference
    FastLanguageModel.for_inference(model)
    
    print("\n" + "="*70)
    print("🎉 SAFETY TRAINING COMPLETE!")
    print("="*70)
    print(f"\n📦 Updated model saved to: {model_save_path}")
    print(f"💾 Safety dataset saved to: {safety_save_path}")
    print(f"📊 TensorBoard logs: {tensorboard_log_dir}")
    
    print("\n📋 NEXT STEPS:")
    print("======================================================================")
    print("1. ✅ Re-run evaluation:")
    print("   modal run evaluate_model.py")
    print("   (Update model path in evaluate_model.py to use safety-trained model)")
    print("\n2. 🧪 Test safety improvements:")
    print("   - Crisis handling")
    print("   - Boundary maintenance")
    print("   - Harmful reinforcement prevention")
    print("\n3. 📊 Compare results with previous evaluation")
    print("======================================================================")
    
    return f"Safety training complete! Model saved to {model_save_path}"

@app.local_entrypoint()
def main():
    print("="*70)
    print("🛡️  Starting Safety-Focused Training")
    print("="*70)
    print("\n⚡ This will:")
    print("  • Load your existing fine-tuned model")
    print("  • Add safety-focused training examples")
    print("  • Continue training with lower learning rate")
    print("  • Save updated model with safety improvements")
    print("\n⏱️  Estimated time: ~10-15 minutes")
    print("💰 Cost: ~$1.50-2.50 (H100 GPU)")
    print("\n📊 MONITORING:")
    print("  • Terminal: Watch logs below")
    print("  • Dashboard: https://modal.com/apps")
    print("="*70 + "\n")
    
    result = continue_training_with_safety.remote()
    print(f"\n{result}")

