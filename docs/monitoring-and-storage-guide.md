# Monitoring & Storage Guide

## 📊 Visual Monitoring Options

### 1. Modal Dashboard (Primary - Best Option)

**Access:** https://modal.com/apps

**Features:**
- ✅ Real-time GPU usage graphs
- ✅ Training logs (live streaming)
- ✅ Cost tracking in real-time
- ✅ Function status and execution history
- ✅ Volume contents and sizes
- ✅ Error logs and debugging info

**How to Use:**
1. Open https://modal.com/apps in your browser
2. Click on your app: `qwen-therapist-finetune`
3. View active functions and their status
4. Click on a function to see:
   - Live logs
   - GPU utilization
   - Memory usage
   - Execution time
   - Costs

**Pro Tip:** Keep the dashboard open in a separate tab while training!

---

### 2. Terminal Logs (Real-time)

**What You See:**
- Training loss updates every step
- Progress indicators
- Status messages with emojis (🚀, ✅, 📊, etc.)
- Error messages if something goes wrong

**Example Output:**
```
🚀 Training started!
📈 Watch for loss values decreasing over time
{'loss': 1.234, 'learning_rate': 0.0002, 'epoch': 0.1}
{'loss': 1.123, 'learning_rate': 0.0002, 'epoch': 0.2}
...
✅ Training completed!
```

---

### 3. TensorBoard (After Training)

**What It Shows:**
- Training loss curves
- Learning rate schedule
- Step-by-step metrics
- Visual graphs of training progress

**How to Use:**

**Option A: Download and View Locally**
```bash
# Download TensorBoard logs from Modal
modal volume get training-data /tensorboard_logs ./tb_logs

# Start TensorBoard
tensorboard --logdir=./tb_logs

# Open in browser: http://localhost:6006
```

**Option B: Use Helper Script**
```bash
modal run view_tensorboard.py
```

**What You'll See:**
- Loss decreasing over time (good sign!)
- Learning rate schedule
- Training metrics
- Step-by-step progress

---

### 4. Monitor Training Script

**Quick Reference:**
```bash
modal run monitor_training.py
```

Shows you:
- Links to Modal dashboard
- How to access different monitoring tools
- Tips for monitoring training
- Status information

---

## 💾 Storage on Modal Volumes

### What Gets Stored

**1. Trained Models**
- Location: `/data/qwen_therapist_lora/`
- Contains:
  - `adapter_config.json` - LoRA configuration
  - `adapter_model.safetensors` - Trained weights
  - `tokenizer files` - Tokenizer configuration
- Size: ~100-200 MB (LoRA adapters are small!)

**2. Dataset Cache**
- Location: `/data/datasets_cache/`
- Contains: Cached Hugging Face dataset
- Benefit: **Much faster on subsequent runs!**
- First run: Downloads dataset
- Future runs: Uses cached version (instant!)

**3. Training Checkpoints**
- Location: `/data/outputs/checkpoint-*/`
- Contains: Model checkpoints during training
- Saved every 100 steps (configurable)
- Useful for: Resuming training or selecting best checkpoint

**4. TensorBoard Logs**
- Location: `/data/tensorboard_logs/`
- Contains: Training metrics and visualizations
- Use for: Analyzing training progress

---

### Managing Storage

**List Volume Contents:**
```bash
modal volume ls training-data
```

**See What's Stored:**
```bash
# List all files
modal volume ls training-data

# List specific directory
modal volume ls training-data /qwen_therapist_lora

# List dataset cache
modal volume ls training-data /datasets_cache
```

**Download from Volume:**
```bash
# Download entire model
modal volume get training-data /qwen_therapist_lora ./local_model

# Download specific file
modal volume get training-data /qwen_therapist_lora/adapter_config.json ./

# Download TensorBoard logs
modal volume get training-data /tensorboard_logs ./tb_logs
```

**Upload to Volume:**
```bash
# Upload a file
modal volume put training-data ./my_file.txt /my_file.txt

# Upload a directory
modal volume put training-data ./my_data /datasets/
```

**Check Volume Size:**
- View in Modal dashboard: https://modal.com/apps
- Click on "Volumes" section
- See size and usage for each volume

---

## 📈 Visual Status Indicators

### During Training

**Terminal Output:**
```
[1/6] Loading Qwen2.5-7B-Instruct model...     ✓ Model loaded
[2/6] Setting up LoRA...                      ✓ LoRA configured
[3/6] Loading dataset...                      ✓ Dataset loaded: 1234 examples
[4/6] Formatting dataset...                  ✓ Dataset formatted
[5/6] Starting training...                    🚀 Training started!
[6/6] Saving model...                         ✓ Model saved
```

**Status Emojis:**
- 🚀 Starting/In Progress
- ✅ Completed Successfully
- 📊 Monitoring/Logging
- 💾 Saving/Storage
- ⚡ Fast/Cached
- 📥 Downloading
- 📈 Progress/Improvement
- ⚠️ Warning
- ❌ Error

---

## 🎯 Quick Monitoring Checklist

**Before Training:**
- [ ] Open Modal dashboard: https://modal.com/apps
- [ ] Have terminal ready to watch logs
- [ ] Know where to find TensorBoard logs

**During Training:**
- [ ] Watch terminal for loss updates
- [ ] Check Modal dashboard for GPU usage
- [ ] Monitor costs in dashboard
- [ ] Verify checkpoints are saving

**After Training:**
- [ ] Check model saved: `modal volume ls training-data`
- [ ] View TensorBoard logs (optional)
- [ ] Review training metrics
- [ ] Test inference

---

## 💡 Pro Tips

1. **Keep Dashboard Open**: Best way to monitor everything
2. **Dataset Caching**: First run downloads, future runs are instant!
3. **Checkpoint Management**: Delete old checkpoints to save space
4. **TensorBoard**: Great for analyzing training curves
5. **Volume Management**: Regularly check what's stored to manage costs

---

## 🔗 Quick Links

- **Modal Dashboard**: https://modal.com/apps
- **Volume Management**: `modal volume --help`
- **TensorBoard**: Install locally with `pip install tensorboard`
- **Monitoring Script**: `modal run monitor_training.py`

---

## 📊 Example Monitoring Workflow

1. **Start Training:**
   ```bash
   modal run train_qwen_therapist_lora.py
   ```

2. **Open Dashboard:**
   - Go to https://modal.com/apps
   - Click on `qwen-therapist-finetune`
   - Watch GPU usage and logs

3. **Watch Terminal:**
   - See loss values updating
   - Monitor progress indicators

4. **After Training:**
   - Check model saved
   - Download TensorBoard logs (optional)
   - View training curves

5. **Test Model:**
   ```bash
   modal run test_inference.py
   ```

---

**Everything is stored on Modal - no local storage needed unless you download!**

