"""
Test inference with the fine-tuned therapist model.
Run: modal run test_inference.py
"""
import modal

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")  # Need git to install unsloth
    .pip_install(
        "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git",
        "transformers",
        "accelerate",
        "bitsandbytes",
        "xformers",
        "torchvision",  # Required by unsloth
    )
)

app = modal.App("test-inference")

training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

@app.function(
    image=image,
    gpu="A10G",
    volumes={"/data": training_volume},  # Same volume where model is stored
    timeout=600,  # 10 minutes for inference
)
def inference(prompt: str):
    """Run inference using the fine-tuned model - all on Modal!"""
    from unsloth import FastLanguageModel
    import torch
    
    print(f"Loading fine-tuned model from Modal volume...")
    
    print(f"Loading fine-tuned model from Modal volume...")
    # Load the fine-tuned model from Modal volume
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="/data/qwen_therapist_lora",  # Path on Modal volume
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    
    # Enable fast inference
    FastLanguageModel.for_inference(model)
    
    # Format prompt
    messages = [{"role": "user", "content": prompt}]
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to("cuda")
    
    # Generate
    print("Generating response...")
    outputs = model.generate(
        input_ids=inputs,
        max_new_tokens=256,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
    )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

@app.function(
    image=image,
    gpu="A10G",
    volumes={"/data": training_volume},
    timeout=600,
)
def test_multiple_prompts():
    """Test the model with multiple therapeutic prompts"""
    from unsloth import FastLanguageModel
    import torch
    
    print("="*70)
    print("Testing Fine-Tuned Therapist Model")
    print("="*70)
    
    # Load model once
    print("\nLoading model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="/data/qwen_therapist_lora",
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    print("✓ Model loaded")
    
    # Test prompts
    test_prompts = [
        "I've been feeling really anxious lately. Can you help me understand what might be causing this?",
        "How do I deal with stress at work?",
        "What are some coping strategies for depression?",
        "I'm having trouble sleeping. What can I do?",
    ]
    
    results = []
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_prompts)}")
        print(f"{'='*70}")
        print(f"Prompt: {prompt}\n")
        
        messages = [{"role": "user", "content": prompt}]
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to("cuda")
        
        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
        )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract just the assistant's response
        if "assistant" in response.lower():
            response = response.split("assistant")[-1].strip()
        
        print(f"Response: {response}\n")
        results.append({"prompt": prompt, "response": response})
    
    print("="*70)
    print("Inference Testing Complete!")
    print("="*70)
    
    return results

@app.local_entrypoint()
def main():
    print("Testing inference with fine-tuned model...")
    print("This will test multiple therapeutic prompts.\n")
    results = test_multiple_prompts.remote()
    
    print("\n" + "="*70)
    print("All Test Results:")
    print("="*70)
    for i, result in enumerate(results, 1):
        print(f"\nTest {i}:")
        print(f"  Prompt: {result['prompt']}")
        print(f"  Response: {result['response'][:200]}...")

