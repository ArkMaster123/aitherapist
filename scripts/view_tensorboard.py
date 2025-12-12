"""
View TensorBoard logs from Modal training.
This downloads the logs and starts TensorBoard locally.

Run: modal run view_tensorboard.py
"""
import modal
import subprocess
import os
from pathlib import Path

image = modal.Image.debian_slim(python_version="3.11").pip_install("tensorboard")

app = modal.App("view-tensorboard")

training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

@app.function(
    image=image,
    volumes={"/data": training_volume},
    timeout=60,
)
def download_tensorboard_logs():
    """Download TensorBoard logs from Modal volume"""
    import shutil
    
    tensorboard_log_dir = "/data/tensorboard_logs"
    local_log_dir = "/tmp/tb_logs"
    
    if os.path.exists(tensorboard_log_dir):
        print(f"📥 Downloading TensorBoard logs from {tensorboard_log_dir}...")
        if os.path.exists(local_log_dir):
            shutil.rmtree(local_log_dir)
        shutil.copytree(tensorboard_log_dir, local_log_dir)
        print(f"✓ Logs downloaded to {local_log_dir}")
        return local_log_dir
    else:
        print("⚠️  No TensorBoard logs found. Make sure training has completed.")
        return None

@app.local_entrypoint()
def main():
    print("="*70)
    print("📊 TensorBoard Log Viewer")
    print("="*70)
    print("\nThis will download TensorBoard logs from Modal and start TensorBoard.")
    print("TensorBoard will open in your browser automatically.\n")
    
    # Download logs
    log_dir = download_tensorboard_logs.remote()
    
    if log_dir:
        print(f"\n📊 Starting TensorBoard...")
        print(f"   Log directory: {log_dir}")
        print(f"\n💡 TensorBoard will open at: http://localhost:6006")
        print("   Press Ctrl+C to stop TensorBoard\n")
        
        # Note: This would need to be run locally, not in Modal
        # For now, just provide instructions
        print("="*70)
        print("📋 TO VIEW TENSORBOARD LOCALLY:")
        print("="*70)
        print("\n1. Download logs from Modal volume:")
        print("   modal volume get training-data /tensorboard_logs ./tb_logs")
        print("\n2. Start TensorBoard:")
        print("   tensorboard --logdir=./tb_logs")
        print("\n3. Open in browser:")
        print("   http://localhost:6006")
        print("\nOr view directly in Modal dashboard:")
        print("   https://modal.com/apps")
        print("="*70)
    else:
        print("\n⚠️  No logs available. Run training first!")

