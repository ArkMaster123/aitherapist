#!/usr/bin/env python3
"""
Download evaluation results from Modal volume for comparison.
"""
import modal
import os
import shutil
from pathlib import Path

app = modal.App("download-evaluation-results")
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11")

@app.function(
    image=image,
    volumes={"/data": training_volume},
)
def download_evaluation_results():
    """Download evaluation results from Modal volume"""
    import json
    
    evaluation_path = "/data/evaluation_results.json"
    
    if not os.path.exists(evaluation_path):
        print(f"❌ Evaluation results not found at {evaluation_path}")
        return None
    
    print(f"📖 Reading evaluation results from {evaluation_path}...")
    with open(evaluation_path, 'r') as f:
        results = json.load(f)
    
    print(f"✅ Loaded evaluation results")
    print(f"   Total examples: {results.get('total_examples', 'N/A')}")
    print(f"   Evaluated: {results.get('evaluated', 'N/A')}")
    
    return results

@app.local_entrypoint()
def main():
    print("="*70)
    print("📥 Downloading Evaluation Results from Modal")
    print("="*70)
    
    results = download_evaluation_results.remote()
    
    if results:
        # Save to local file
        output_path = "evaluation_results_safety.json"
        with open(output_path, 'w') as f:
            import json
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Evaluation results saved to: {output_path}")
        print("\n📊 Summary:")
        print("="*70)
        
        if "metrics" in results:
            print("\n📈 Metrics:")
            for key, value in results["metrics"].items():
                if value is not None:
                    print(f"   {key}: {value}")
        
        if "safety_tests" in results:
            print("\n🛡️  Safety Tests:")
            for test_name, passed in results["safety_tests"].items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"   {test_name}: {status}")
        
        print("\n💡 Compare with previous evaluation:")
        print("   diff evaluation_results.json evaluation_results_safety.json")
        print("   OR open both files side-by-side")
        print("="*70)
    else:
        print("❌ Failed to download evaluation results")

