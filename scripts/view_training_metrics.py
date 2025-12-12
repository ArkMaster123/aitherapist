#!/usr/bin/env python3
"""
View training metrics from TensorBoard logs.
Shows loss curves, learning rate, and training progress.

Usage: modal run view_training_metrics.py
"""
import modal
import os
from pathlib import Path

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "tensorboard",
        "pandas",
        "numpy",
        "matplotlib",
    )
)

app = modal.App("view-training-metrics")
training_volume = modal.Volume.from_name("training-data", create_if_missing=True)

@app.function(
    image=image,
    volumes={"/data": training_volume},
    timeout=600,
)
def analyze_training_metrics():
    """Analyze TensorBoard logs and generate report"""
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
    import json
    from pathlib import Path
    
    print("="*70)
    print("📊 Training Metrics Analysis")
    print("="*70)
    
    log_dir = Path("/data/tensorboard_logs")
    
    if not log_dir.exists():
        print("❌ TensorBoard logs not found!")
        print(f"   Expected: {log_dir}")
        print("\n💡 Training logs should be at /data/tensorboard_logs")
        print("   If you haven't trained yet, run: modal run train_qwen_therapist_lora.py")
        return
    
    print(f"\n📁 Loading logs from: {log_dir}")
    
    # Find event files
    event_files = list(log_dir.rglob("events.out.tfevents.*"))
    if not event_files:
        print("❌ No TensorBoard event files found!")
        return
    
    print(f"✅ Found {len(event_files)} event file(s)")
    
    # Load events
    ea = EventAccumulator(str(log_dir))
    ea.Reload()
    
    # Get available tags
    tags = ea.Tags()
    print(f"\n📋 Available metrics: {list(tags.get('scalars', []))}")
    
    metrics = {}
    
    # Extract loss
    if 'train/loss' in tags.get('scalars', []):
        loss_events = ea.Scalars('train/loss')
        metrics['loss'] = {
            'values': [e.value for e in loss_events],
            'steps': [e.step for e in loss_events],
            'final': loss_events[-1].value if loss_events else None,
            'initial': loss_events[0].value if loss_events else None,
        }
        print(f"\n📉 Training Loss:")
        print(f"   Initial: {metrics['loss']['initial']:.4f}")
        print(f"   Final: {metrics['loss']['final']:.4f}")
        print(f"   Change: {metrics['loss']['initial'] - metrics['loss']['final']:.4f}")
        print(f"   Steps: {len(loss_events)}")
        
        # Check convergence
        if len(loss_events) > 10:
            recent_losses = [e.value for e in loss_events[-10:]]
            loss_std = sum((x - sum(recent_losses)/len(recent_losses))**2 for x in recent_losses) / len(recent_losses)
            if loss_std < 0.01:
                print(f"   ✅ Loss appears converged (std: {loss_std:.4f})")
            else:
                print(f"   ⚠️  Loss may not be fully converged (std: {loss_std:.4f})")
    
    # Extract learning rate
    if 'train/learning_rate' in tags.get('scalars', []):
        lr_events = ea.Scalars('train/learning_rate')
        metrics['learning_rate'] = {
            'values': [e.value for e in lr_events],
            'steps': [e.step for e in lr_events],
        }
        print(f"\n📈 Learning Rate:")
        print(f"   Initial: {lr_events[0].value:.2e}")
        print(f"   Final: {lr_events[-1].value:.2e}")
    
    # Save metrics
    metrics_path = Path("/data/training_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    
    print(f"\n💾 Metrics saved to: {metrics_path}")
    print("\n" + "="*70)
    print("📋 Summary")
    print("="*70)
    print("\n✅ Training metrics analyzed")
    print("\n💡 To view TensorBoard locally:")
    print("   1. Download logs: modal volume get training-data /tensorboard_logs ./tb_logs")
    print("   2. Run: tensorboard --logdir=./tb_logs")
    print("   3. Open: http://localhost:6006")
    print("="*70)
    
    return metrics

@app.local_entrypoint()
def main():
    analyze_training_metrics.remote()

