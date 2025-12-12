#!/usr/bin/env python3
"""
Upload safety training dataset to Modal volume.
Run this first before continue_training_with_safety.py
"""
import modal
import json
import os

app = modal.App("upload-safety-dataset")
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11")

@app.function(
    image=image,
    volumes={"/data": training_volume},
)
def upload_safety_dataset(safety_data_json: str):
    """Upload safety dataset to Modal volume - receives JSON as string"""
    import json
    
    # Parse JSON string
    safety_data = json.loads(safety_data_json)
    
    # Save to volume
    volume_path = "/data/safety_training_dataset.json"
    with open(volume_path, 'w') as f:
        json.dump(safety_data, f, indent=2)
    
    print(f"✅ Safety dataset uploaded to volume: {volume_path}")
    print(f"   Total examples: {len(safety_data)}")
    return f"Uploaded {len(safety_data)} examples to {volume_path}"

@app.local_entrypoint()
def main():
    # Read file locally
    local_path = "safety_training_dataset.json"
    if not os.path.exists(local_path):
        print(f"❌ File not found: {local_path}")
        print("   Please ensure safety_training_dataset.json is in the current directory")
        return
    
    print(f"📖 Reading local file: {local_path}")
    with open(local_path, 'r') as f:
        safety_data = json.load(f)
    
    print(f"✅ Loaded {len(safety_data)} examples from local file")
    print("📤 Uploading to Modal volume...")
    
    # Convert to JSON string for transmission
    safety_data_json = json.dumps(safety_data)
    
    # Upload to volume
    result = upload_safety_dataset.remote(safety_data_json)
    print(f"\n{result}")
    print("\n✅ Ready to run: modal run continue_training_with_safety.py")
