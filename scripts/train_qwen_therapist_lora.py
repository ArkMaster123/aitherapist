"""
Fine-tune Qwen2.5-7B-Instruct using LoRA on therapist_conversations dataset.
Run: modal run train_qwen_therapist_lora.py

Everything runs remotely on Modal - no local GPU needed!

Features:
- Dataset cached to Modal volume (faster subsequent runs)
- TensorBoard logging for visual monitoring
- Progress indicators and status updates
- Modal dashboard integration
"""
import modal
import os

# These imports will be available in Modal's cloud environment
# Import them inside the function to avoid local import errors

# All packages install automatically in Modal's cloud
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")  # Need git to install unsloth from GitHub
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
        "tensorboard",  # For visual monitoring
        "tqdm",  # For progress bars
        "torchvision",  # Required by unsloth
    )
)

app = modal.App("qwen-therapist-finetune")

# Persistent volume - your model stays here!
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

@app.function(
    image=image,
    gpu="H100",  # H100 for FAST training! 80GB VRAM, much faster than A10G
    timeout=1800,  # 30 minutes max (should finish in ~10 mins)
    secrets=[modal.Secret.from_name("huggingface-secret")],  # For accessing Hugging Face datasets
    volumes={"/data": training_volume},
)
def train_qwen_therapist():
    """Fine-tune Qwen2.5-7B on therapist conversations - runs entirely on Modal!"""
    # Import here - these are available in Modal's environment
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import load_dataset
    import torch
    from pathlib import Path
    
    print("="*70)
    print("Fine-tuning Qwen2.5-7B-Instruct for Therapist Conversations")
    print("="*70)
    
    # Load Qwen model - H100 has 80GB VRAM, so we can use less quantization for speed!
    print("\n[1/6] Loading Qwen2.5-7B-Instruct model...")
    print("🚀 Using H100 GPU - Optimized for SPEED!")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="Qwen/Qwen2.5-7B-Instruct",
        max_seq_length=2048,
        dtype=torch.bfloat16,  # Use bfloat16 on H100 for faster training
        load_in_4bit=False,  # H100 has enough VRAM - no quantization needed for speed!
    )
    print("✓ Model loaded (no quantization - maximum speed!)")
    
    # Enable optimizations - H100 can handle larger batches and faster training
    print("\n[2/6] Setting up LoRA (optimized for H100 speed)...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,  # LoRA rank
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing=False,  # Disable for speed (H100 has enough memory)
        random_state=3407,
    )
    print("✓ LoRA configured (optimized for H100)")
    
    # Load therapist conversations dataset (with caching to Modal volume)
    print("\n[3/6] Loading therapist_conversations dataset...")
    
    # Set cache directory to Modal volume for persistent storage
    dataset_cache_dir = "/data/datasets_cache"
    os.makedirs(dataset_cache_dir, exist_ok=True)
    
    # Load dataset (will cache to volume for faster subsequent runs)
    print("  📥 Downloading dataset (first time only, then cached)...")
    dataset = load_dataset(
        "Jyz1331/therapist_conversations",
        cache_dir=dataset_cache_dir
    )
    
    # Get the training split
    split_name = "train" if "train" in dataset else list(dataset.keys())[0]
    train_dataset = dataset[split_name]
    
    print(f"✓ Dataset loaded: {len(train_dataset)} examples")
    print(f"  Split: {split_name}")
    print(f"  First example keys: {list(train_dataset[0].keys())}")
    print(f"  💾 Dataset cached to: {dataset_cache_dir}")
    print(f"  ⚡ Future runs will use cached dataset (much faster!)")
    
    # Format dataset for Qwen's chat template
    # This function adapts to different dataset formats
    print("\n[4/6] Formatting dataset for Qwen chat template...")
    
    def formatting_prompts_func(examples):
        texts = []
        
        # Try different common dataset formats
        if "conversation" in examples:
            # Format: {"conversation": [{"role": "user", "content": "..."}, ...]}
            for conv in examples["conversation"]:
                text = tokenizer.apply_chat_template(
                    conv,
                    tokenize=False,
                    add_generation_prompt=False,
                )
                texts.append(text)
                
        elif "messages" in examples:
            # Format: {"messages": [{"role": "user", "content": "..."}, ...]}
            for messages in examples["messages"]:
                text = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=False,
                )
                texts.append(text)
                
        elif "instruction" in examples and "output" in examples:
            # Format: {"instruction": "...", "output": "..."}
            for instruction, output in zip(examples["instruction"], examples["output"]):
                text = tokenizer.apply_chat_template(
                    [{"role": "user", "content": instruction},
                     {"role": "assistant", "content": output}],
                    tokenize=False,
                    add_generation_prompt=False,
                )
                texts.append(text)
                
        elif "user" in examples and "assistant" in examples:
            # Format: {"user": "...", "assistant": "..."}
            for user, assistant in zip(examples["user"], examples["assistant"]):
                text = tokenizer.apply_chat_template(
                    [{"role": "user", "content": user},
                     {"role": "assistant", "content": assistant}],
                    tokenize=False,
                    add_generation_prompt=False,
                )
                texts.append(text)
        elif "question" in examples and "response" in examples:
            # Format: {"question": "...", "response": "..."}
            for question, response in zip(examples["question"], examples["response"]):
                text = tokenizer.apply_chat_template(
                    [{"role": "user", "content": question},
                     {"role": "assistant", "content": response}],
                    tokenize=False,
                    add_generation_prompt=False,
                )
                texts.append(text)
        else:
            # Show available keys for debugging
            available_keys = list(examples.keys())
            raise ValueError(
                f"Unknown dataset format. Available keys: {available_keys}\n"
                f"Please inspect the dataset first and adapt the formatting function."
            )
        
        return {"text": texts}
    
    train_dataset = train_dataset.map(formatting_prompts_func, batched=True)
    print("✓ Dataset formatted")
    
    # Training arguments optimized for therapeutic conversations
    print("\n[5/6] Starting training...")
    print("\n" + "="*70)
    print("📊 MONITORING OPTIONS:")
    print("="*70)
    print("1. Terminal: Watch logs below for real-time progress")
    print("2. Modal Dashboard: https://modal.com/apps")
    print("   - See GPU usage, logs, and metrics")
    print("   - Track costs in real-time")
    print("3. TensorBoard: Logs saved to /data/tensorboard_logs")
    print("="*70 + "\n")
    
    # TensorBoard logging directory
    tensorboard_log_dir = "/data/tensorboard_logs"
    os.makedirs(tensorboard_log_dir, exist_ok=True)
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        packing=False,
        args=TrainingArguments(
            # H100 OPTIMIZED FOR SPEED - Larger batches, less accumulation
            per_device_train_batch_size=8,  # Increased from 2 (H100 has 80GB VRAM!)
            gradient_accumulation_steps=2,  # Reduced from 4 (larger batch size)
            warmup_steps=5,  # Reduced warmup for speed
            num_train_epochs=1,  # 1 epoch should be enough
            learning_rate=2e-4,
            fp16=False,  # Use bfloat16 on H100
            bf16=True,  # H100 supports bfloat16 natively - faster!
            logging_steps=10,  # Log every 10 steps (less frequent for speed)
            optim="adamw_torch",  # Use full precision optimizer (H100 can handle it)
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=3407,
            output_dir="/data/outputs",
            save_steps=500,  # Save less frequently for speed
            # Visual monitoring
            logging_dir=tensorboard_log_dir,
            report_to="tensorboard",
            run_name="qwen-therapist-lora-h100",
            # Speed optimizations
            dataloader_num_workers=4,  # Parallel data loading
            dataloader_pin_memory=True,  # Faster data transfer
            remove_unused_columns=False,  # Keep columns for speed
        ),
    )
    
    # Train with progress indicators
    print("🚀 Training started on H100 GPU!")
    print("⚡ Optimized for SPEED - should complete in ~10 minutes!")
    print("📈 Watch for loss values decreasing over time")
    print("💡 Tip: Open Modal dashboard in another tab to see GPU usage\n")
    
    trainer.train()
    
    print("\n" + "="*70)
    print("✅ Training completed!")
    print("="*70)
    print(f"📊 TensorBoard logs: {tensorboard_log_dir}")
    print("   View with: tensorboard --logdir=/data/tensorboard_logs")
    
    # Save model
    print("\n[6/6] Saving fine-tuned model...")
    model_save_path = "/data/qwen_therapist_lora"
    model.save_pretrained(model_save_path)
    tokenizer.save_pretrained(model_save_path)
    print(f"✓ Model saved to {model_save_path}")
    
    # Optimize for inference
    FastLanguageModel.for_inference(model)
    
    print("\n" + "="*70)
    print("🎉 TRAINING COMPLETE!")
    print("="*70)
    print(f"\n📦 Model saved to Modal volume: {model_save_path}")
    print(f"💾 Dataset cached to: {dataset_cache_dir}")
    print(f"📊 TensorBoard logs: {tensorboard_log_dir}")
    
    # Show what's stored on the volume
    print("\n📁 Contents on Modal volume:")
    volume_contents = []
    for root, dirs, files in os.walk("/data"):
        level = root.replace("/data", "").count(os.sep)
        indent = " " * 2 * level
        folder_name = os.path.basename(root) if root != "/data" else "training-data"
        volume_contents.append(f"{indent}{folder_name}/")
        subindent = " " * 2 * (level + 1)
        for file in files[:5]:  # Show first 5 files
            volume_contents.append(f"{subindent}{file}")
        if len(files) > 5:
            volume_contents.append(f"{subindent}... and {len(files) - 5} more files")
    
    for item in volume_contents[:20]:  # Limit output
        print(item)
    
    print("\n" + "="*70)
    print("📋 NEXT STEPS:")
    print("="*70)
    print("1. ✅ Verify model saved:")
    print("   modal volume ls training-data")
    print("\n2. 🧪 Test inference:")
    print("   modal run test_inference.py")
    print("\n3. 📊 View TensorBoard logs (if downloaded):")
    print("   modal volume get training-data /tensorboard_logs ./tb_logs")
    print("   tensorboard --logdir=./tb_logs")
    print("\n4. 🌐 Check Modal Dashboard:")
    print("   https://modal.com/apps")
    print("   - View GPU usage history")
    print("   - See cost breakdown")
    print("   - Access logs")
    print("\n5. 💾 Download model (if needed):")
    print("   modal volume get training-data /qwen_therapist_lora ./local_model")
    print("="*70)
    
    return {
        "status": "complete",
        "model_path": model_save_path,
        "dataset_cache": dataset_cache_dir,
        "tensorboard_logs": tensorboard_log_dir,
        "message": f"Training complete! Model saved to {model_save_path}"
    }

# Entry point - everything runs remotely on Modal
@app.local_entrypoint()
def main():
    print("="*70)
    print("🚀 Starting FAST Training on Modal H100 GPU")
    print("="*70)
    print("\n⚡ Using H100 GPU - Optimized for SPEED!")
    print("⏱️  Estimated time: ~10 minutes (vs 1-2 hours on A10G)")
    print("💰 Cost: ~$1.50-2.00 (H100 is ~$8-10/hour)")
    print("\n📊 MONITORING:")
    print("  • Terminal: Watch logs below for real-time progress")
    print("  • Dashboard: https://modal.com/apps")
    print("  • TensorBoard: Logs saved to Modal volume")
    print("\n💡 Optimizations:")
    print("  • H100 GPU (80GB VRAM)")
    print("  • No quantization (full bfloat16)")
    print("  • Larger batch size (8 vs 2)")
    print("  • Faster data loading")
    print("  • Optimized for speed over memory")
    print("\n" + "="*70 + "\n")
    
    result = train_qwen_therapist.remote()
    
    if isinstance(result, dict):
        print(f"\n✅ {result['message']}")
        print(f"\n📊 View TensorBoard logs: {result['tensorboard_logs']}")
        print(f"🌐 Check Modal Dashboard: https://modal.com/apps")
    else:
        print(f"\n{result}")


