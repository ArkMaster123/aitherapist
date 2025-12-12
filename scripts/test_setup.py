"""
Test script to verify Modal setup and package installation.
Run this first: modal run test_setup.py
"""
import modal

# Define the image with all dependencies
# Everything installs automatically in Modal's cloud - no local installation needed!
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

app = modal.App("test-finetune-setup")

# Create a volume for storing models and data
# This persists across runs - your trained models stay here!
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

@app.function(
    image=image,
    gpu=modal.gpu.H100(),  # Using H100 for speed! (can change to A10G if needed)
    timeout=600,  # 10 minutes for test
    volumes={"/data": training_volume},
)
def test_setup():
    """Test that all packages are installed correctly"""
    print("Testing Modal setup...")
    
    # Test imports
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    import torch
    
    print("✓ All packages imported successfully!")
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
        print(f"✓ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    # Test volume access
    import os
    test_file = "/data/test.txt"
    with open(test_file, "w") as f:
        f.write("Volume test successful!")
    
    # Verify write
    if os.path.exists(test_file):
        with open(test_file, "r") as f:
            content = f.read()
            if "successful" in content:
                print(f"✓ Volume write test successful!")
    
    print("\n" + "="*50)
    print("Setup test PASSED! Ready for fine-tuning.")
    print("="*50)
    
    return "Setup test passed! Ready for fine-tuning."

# Entry point - runs remotely on Modal
@app.local_entrypoint()
def main():
    print("Running setup test on Modal...")
    print("This will verify all packages and GPU access.\n")
    result = test_setup.remote()
    print(f"\n{result}")

