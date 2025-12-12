#!/usr/bin/env python3
"""
Check if safety dataset exists on Modal volume
"""
import modal
import os

app = modal.App("check-safety-dataset")
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11")

@app.function(
    image=image,
    volumes={"/data": training_volume},
)
def check_safety_dataset():
    """Check if safety dataset exists on volume"""
    safety_path = "/data/safety_training_dataset.json"
    
    print(f"Checking for file at: {safety_path}")
    print(f"File exists: {os.path.exists(safety_path)}")
    
    if os.path.exists(safety_path):
        import json
        with open(safety_path, 'r') as f:
            data = json.load(f)
        print(f"✅ File found! Contains {len(data)} examples")
        
        # List all files in /data
        print("\n📁 Files in /data directory:")
        for root, dirs, files in os.walk("/data"):
            level = root.replace("/data", "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    else:
        print("❌ File not found!")
        print("\n📁 Files in /data directory:")
        if os.path.exists("/data"):
            for root, dirs, files in os.walk("/data"):
                level = root.replace("/data", "").count(os.sep)
                indent = " " * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = " " * 2 * (level + 1)
                for file in files:
                    print(f"{subindent}{file}")
        else:
            print("   /data directory does not exist")

@app.local_entrypoint()
def main():
    check_safety_dataset.remote()

