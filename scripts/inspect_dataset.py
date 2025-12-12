"""
Inspect the therapist_conversations dataset structure.
Run: modal run inspect_dataset.py
"""
import modal
from datasets import load_dataset

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("datasets", "huggingface_hub")
)

app = modal.App("inspect-dataset")

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("hf-token")],  # For accessing Hugging Face datasets
    timeout=300,  # 5 minutes
)
def inspect():
    """Inspect the therapist_conversations dataset structure"""
    print("="*60)
    print("Inspecting Jyz1331/therapist_conversations dataset")
    print("="*60)
    
    print("\nLoading dataset...")
    ds = load_dataset("Jyz1331/therapist_conversations")
    
    print(f"\n✓ Dataset loaded successfully!")
    print(f"\nDataset splits: {list(ds.keys())}")
    
    # Get the train split (or first available split)
    split_name = "train" if "train" in ds else list(ds.keys())[0]
    train_data = ds[split_name]
    
    print(f"\nUsing split: '{split_name}'")
    print(f"Number of examples: {len(train_data)}")
    
    # Show first example
    print(f"\n{'='*60}")
    print("First Example Structure:")
    print("="*60)
    first_example = train_data[0]
    
    for key, value in first_example.items():
        value_str = str(value)
        if len(value_str) > 300:
            value_str = value_str[:300] + "..."
        print(f"\n  Key: '{key}'")
        print(f"  Type: {type(value).__name__}")
        print(f"  Value: {value_str}")
    
    # Show a few more examples to understand pattern
    print(f"\n{'='*60}")
    print("Sample of Multiple Examples:")
    print("="*60)
    for i in range(min(3, len(train_data))):
        print(f"\n--- Example {i+1} ---")
        example = train_data[i]
        for key in list(example.keys())[:3]:  # Show first 3 keys
            value = str(example[key])
            if len(value) > 150:
                value = value[:150] + "..."
            print(f"  {key}: {value}")
    
    print(f"\n{'='*60}")
    print("Dataset Inspection Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Note the field names (keys) in the examples above")
    print("2. Understand how conversations are structured")
    print("3. Use this info to format the dataset for training")
    
    return {
        "splits": list(ds.keys()),
        "train_size": len(train_data),
        "example_keys": list(first_example.keys()),
        "first_example": {k: str(v)[:200] for k, v in first_example.items()}
    }

@app.local_entrypoint()
def main():
    print("Inspecting dataset on Modal...")
    print("This will show you the dataset structure.\n")
    result = inspect.remote()
    print(f"\nInspection result: {result}")

