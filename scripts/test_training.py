"""
Quick test training with tiny dataset to verify training loop works.
Run: modal run test_training.py
"""
import modal
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import Dataset
import torch

image = (
    modal.Image.debian_slim(python_version="3.11")
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
    )
)

app = modal.App("test-training")

training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

@app.function(
    image=image,
    gpu=modal.gpu.H100(),  # Use H100 for speed even in testing!
    timeout=600,  # 10 minutes for test (H100 is fast!)
    volumes={"/data": training_volume},
    secrets=[modal.Secret.from_name("hf-token")],
)
def test_training():
    """Quick test training with just 5 examples"""
    print("="*60)
    print("Starting TEST training (5 steps only)")
    print("="*60)
    
    # Load a small model for testing
    print("\nLoading Qwen2.5-1.5B-Instruct (small model for testing)...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="Qwen/Qwen2.5-1.5B-Instruct",  # Very small for quick test
        max_seq_length=512,  # Shorter for testing
        dtype=None,
        load_in_4bit=True,
    )
    print("✓ Model loaded")
    
    # Setup LoRA
    print("\nSetting up LoRA...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=8,  # Lower rank for testing
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_alpha=8,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing=True,
    )
    print("✓ LoRA configured")
    
    # Create tiny test dataset
    print("\nCreating test dataset (5 examples)...")
    test_data = {
        "instruction": [
            "What is therapy?",
            "How can I manage anxiety?",
            "What are coping strategies?",
            "How do I deal with stress?",
            "What is cognitive behavioral therapy?"
        ],
        "output": [
            "Therapy is a treatment method that helps people understand and work through their emotional and psychological challenges.",
            "Anxiety can be managed through techniques like deep breathing, mindfulness, and gradual exposure to feared situations.",
            "Coping strategies include exercise, meditation, talking to friends, and seeking professional help when needed.",
            "Stress can be managed by identifying triggers, practicing relaxation techniques, and maintaining a healthy work-life balance.",
            "Cognitive behavioral therapy (CBT) is a type of psychotherapy that helps people change negative thought patterns and behaviors."
        ]
    }
    test_dataset = Dataset.from_dict(test_data)
    print(f"✓ Created {len(test_dataset)} test examples")
    
    # Format for Qwen's chat template
    def format_func(examples):
        texts = []
        for inst, out in zip(examples["instruction"], examples["output"]):
            text = tokenizer.apply_chat_template(
                [{"role": "user", "content": inst},
                 {"role": "assistant", "content": out}],
                tokenize=False,
                add_generation_prompt=False,
            )
            texts.append(text)
        return {"text": texts}
    
    print("\nFormatting dataset...")
    test_dataset = test_dataset.map(format_func, batched=True)
    print("✓ Dataset formatted")
    
    # Training arguments
    print("\nStarting training (5 steps only)...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=test_dataset,
        dataset_text_field="text",
        max_seq_length=512,
        args=TrainingArguments(
            per_device_train_batch_size=1,
            gradient_accumulation_steps=2,
            max_steps=5,  # Just 5 steps for testing!
            learning_rate=2e-4,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=1,
            output_dir="/data/test_output",
            save_steps=10,
        ),
    )
    
    # Train
    trainer.train()
    
    # Save test model
    print("\nSaving test model...")
    model.save_pretrained("/data/test_model")
    tokenizer.save_pretrained("/data/test_model")
    print("✓ Test model saved to /data/test_model")
    
    print("\n" + "="*60)
    print("✓ TEST TRAINING COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\nNext steps:")
    print("1. Check that model saved: modal volume ls training-data")
    print("2. If successful, proceed to full training!")
    
    return "Test training passed! Ready for full training."

@app.local_entrypoint()
def main():
    print("Running test training on Modal...")
    print("This will train for just 5 steps to verify everything works.\n")
    result = test_training.remote()
    print(f"\n{result}")

