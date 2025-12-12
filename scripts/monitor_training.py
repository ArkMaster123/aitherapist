"""
Monitor training progress in real-time.
Shows status, logs, and provides links to Modal dashboard.

Run: modal run monitor_training.py
"""
import modal
import time
from datetime import datetime

app = modal.App("monitor-training")

@app.function(
    image=modal.Image.debian_slim(),
    timeout=60,
)
def get_training_status():
    """Get current training status and information"""
    return {
        "timestamp": datetime.now().isoformat(),
        "status": "Use this to monitor your training",
        "dashboard_url": "https://modal.com/apps",
    }

@app.local_entrypoint()
def main():
    print("="*70)
    print("📊 Training Monitor")
    print("="*70)
    print("\nThis script helps you monitor your training progress.\n")
    
    print("🌐 MODAL DASHBOARD:")
    print("   https://modal.com/apps")
    print("\n   Features:")
    print("   - Real-time GPU usage")
    print("   - Training logs")
    print("   - Cost tracking")
    print("   - Function status")
    
    print("\n" + "="*70)
    print("📋 MONITORING OPTIONS:")
    print("="*70)
    print("\n1. 📺 Modal Dashboard (Best Option)")
    print("   - Open: https://modal.com/apps")
    print("   - Click on your app: 'qwen-therapist-finetune'")
    print("   - View real-time logs, GPU usage, and metrics")
    
    print("\n2. 💻 Terminal Logs")
    print("   - Training logs stream to your terminal")
    print("   - Watch for loss values decreasing")
    print("   - Look for progress indicators")
    
    print("\n3. 📊 TensorBoard (After Training)")
    print("   - Logs saved to Modal volume")
    print("   - Download: modal volume get training-data /tensorboard_logs ./tb_logs")
    print("   - View: tensorboard --logdir=./tb_logs")
    
    print("\n4. 📁 Volume Contents")
    print("   - Check what's saved: modal volume ls training-data")
    print("   - See model checkpoints: modal volume ls training-data /outputs")
    
    print("\n" + "="*70)
    print("💡 TIPS:")
    print("="*70)
    print("• Keep Modal dashboard open in a browser tab")
    print("• Watch terminal for real-time loss updates")
    print("• Check GPU utilization in dashboard")
    print("• Monitor costs in dashboard")
    print("• Training loss should decrease over time")
    print("• Expected loss range: 0.5-1.0 (depends on dataset)")
    print("="*70)
    
    print("\n🚀 To start monitoring, run your training:")
    print("   modal run train_qwen_therapist_lora.py")
    print("\nThen open the dashboard to watch progress!")

