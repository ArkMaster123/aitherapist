# LoRA Fine-Tuning Plan: Therapist Conversations Model

**Goal:** Fine-tune Qwen2.5-7B-Instruct using LoRA on the `Jyz1331/therapist_conversations` dataset, running entirely on Modal.ai

**Dataset:** `Jyz1331/therapist_conversations` (requires Hugging Face login)

**Model:** Qwen/Qwen2.5-7B-Instruct with QLoRA (4-bit quantization + LoRA)

**Infrastructure:** Modal.ai (H100 GPU for speed, ~$8-10/hour, ~10 min training = ~$1.50-2.00)

---

## 📋 Complete Checklist

### Phase 1: Setup & Authentication

- [ ] **Install Modal CLI**
  ```bash
  pip install modal
  ```

- [ ] **Authenticate with Modal (Web UI)**
  ```bash
  modal setup
  ```
  - Opens browser for authentication
  - Sign in with Google/GitHub/etc.
  - No manual token management needed!

- [ ] **Get Hugging Face Token**
  - Go to: https://huggingface.co/settings/tokens
  - Create new token (read access is enough for public datasets)
  - Copy token for next step

- [ ] **Create Modal Secret for HF Token**
  ```bash
  modal secret create hf-token HF_TOKEN=your_hf_token_here
  ```
  - This stores your HF token securely in Modal
  - Needed to access the dataset

- [ ] **Verify Authentication**
  ```bash
  modal token current
  ```
  - Should show your Modal token info

---

### Phase 2: Test Setup (Verify Everything Works)

- [ ] **Create `test_setup.py`**
  - Copy the test setup script from the main guide
  - Verifies packages install correctly
  - Tests volume access

- [ ] **Run Setup Test**
  ```bash
  modal run test_setup.py
  ```
  - First run takes ~5-10 minutes (builds container)
  - Should see: ✓ All packages imported successfully
  - Should see: ✓ GPU: NVIDIA A10G
  - Should see: ✓ Volume write test successful!

- [ ] **Fix any errors** (if test fails)
  - Check Modal authentication: `modal setup` again
  - Check HF token secret: `modal secret list`
  - Review error messages in terminal

---

### Phase 3: Dataset Inspection & Preparation

- [ ] **Create `inspect_dataset.py`**
  ```python
  import modal
  from datasets import load_dataset

  image = (
      modal.Image.debian_slim(python_version="3.11")
      .pip_install("datasets", "huggingface_hub")
  )

  app = modal.App("inspect-dataset")

  @app.function(
      image=image,
      secrets=[modal.Secret.from_name("hf-token")],
  )
  def inspect():
      print("Loading therapist_conversations dataset...")
      ds = load_dataset("Jyz1331/therapist_conversations")
      
      print(f"\nDataset keys: {list(ds.keys())}")
      print(f"Train split size: {len(ds['train']) if 'train' in ds else 'N/A'}")
      
      # Show first example
      first_example = ds['train'][0] if 'train' in ds else ds[list(ds.keys())[0]][0]
      print(f"\nFirst example keys: {list(first_example.keys())}")
      print(f"\nFirst example:")
      for key, value in first_example.items():
          print(f"  {key}: {str(value)[:200]}...")
      
      return "Dataset inspection complete"

  @app.local_entrypoint()
  def main():
      result = inspect.remote()
      print(result)
  ```

- [ ] **Run Dataset Inspection**
  ```bash
  modal run inspect_dataset.py
  ```
  - Understand dataset structure
  - Note the field names (e.g., "conversation", "user", "assistant", etc.)
  - Check dataset size

- [ ] **Document Dataset Format**
  - Note: What fields does it have?
  - Note: How are conversations structured?
  - Note: How many examples?

---

### Phase 4: Quick Test Training (5 Steps)

- [ ] **Create `test_training.py`**
  - Use Qwen2.5-1.5B-Instruct (smaller, faster for testing)
  - Train for just 5 steps
  - Use tiny subset of data (5-10 examples)

- [ ] **Run Test Training**
  ```bash
  modal run test_training.py
  ```
  - Should complete in ~5-10 minutes
  - Verify training loop works
  - Check that loss decreases
  - Verify model saves to volume

- [ ] **Verify Test Results**
  - Check logs show training progress
  - Verify model saved: `modal volume ls training-data`
  - If successful, proceed to full training!

---

### Phase 5: Full LoRA Training

- [ ] **Create `train_qwen_therapist_lora.py`**
  - Model: Qwen/Qwen2.5-7B-Instruct
  - Method: LoRA (no quantization - H100 has enough VRAM!)
  - Dataset: Full `Jyz1331/therapist_conversations`
  - GPU: **H100 (80GB VRAM)** - Optimized for SPEED! ⚡

- [ ] **Configure Training Parameters (H100 Optimized)**
  - LoRA rank (r): 16
  - LoRA alpha: 16
  - Learning rate: 2e-4
  - Batch size: **8 per device** (H100 can handle it!)
  - Gradient accumulation: **2** (reduced due to larger batch)
  - Max sequence length: 2048
  - Epochs: 1
  - **No quantization** - Full bfloat16 for speed!
  - **No gradient checkpointing** - H100 has enough memory

- [ ] **Set Up Dataset Formatting Function**
  - Adapt based on dataset inspection results
  - Format for Qwen's chat template
  - Handle conversation structure correctly

- [ ] **Run Full Training**
  ```bash
  modal run train_qwen_therapist_lora.py
  ```
  - First run: ~5-10 min for container build
  - Training: **~10 minutes** ⚡ (H100 GPU optimized for speed!)
  - Monitor in terminal or Modal dashboard
  - **Much faster than A10G!**

- [ ] **Monitor Training**
  - Watch training loss (should decrease)
  - Check GPU usage in Modal dashboard
  - Verify checkpoints are saving
  - Expected loss range: 0.5-1.0 (depends on dataset)

- [ ] **Verify Model Saved**
  ```bash
  modal volume ls training-data
  ```
  - Should see `/qwen_therapist_lora/` directory
  - Should contain: `adapter_config.json`, `adapter_model.safetensors`, etc.

---

### Phase 6: Evaluation & Testing

- [ ] **Create `test_inference.py`**
  - Load fine-tuned model from volume
  - Test with sample therapeutic prompts
  - Verify responses are appropriate

- [ ] **Run Inference Tests**
  ```bash
  modal run test_inference.py
  ```
  - Test prompts:
    - "I've been feeling anxious lately. Can you help?"
    - "How do I deal with stress at work?"
    - "What are some coping strategies for depression?"

- [ ] **Evaluate Response Quality**
  - Check if responses are empathetic
  - Verify therapeutic tone
  - Ensure appropriate length
  - Check for hallucinations or inappropriate content

- [ ] **Adjust if Needed**
  - If responses poor: increase training epochs
  - If overfitting: reduce epochs or add dropout
  - If undertrained: train for more epochs

---

### Phase 7: Model Management

- [ ] **List Saved Models**
  ```bash
  modal volume ls training-data
  ```

- [ ] **Option A: Keep on Modal (Recommended)**
  - Model stays on Modal volume
  - Use for inference on Modal
  - No download needed
  - Persistent storage

- [ ] **Option B: Push to Hugging Face Hub**
  ```python
  # Add to training script
  from huggingface_hub import login
  import os
  
  login(token=os.environ["HF_TOKEN"])
  model.push_to_hub("your-username/qwen-therapist-lora", tokenizer=tokenizer)
  ```

- [ ] **Option C: Download Locally (if needed)**
  ```bash
  modal volume get training-data /qwen_therapist_lora ./local_model
  ```

- [ ] **Option D: Export for Other Formats**
  - GGUF for Ollama
  - Standard format for vLLM
  - Keep exports on Modal volume

---

### Phase 8: Deployment & Usage

- [ ] **Create Production Inference Function**
  - Optimize for speed
  - Add error handling
  - Set up proper timeouts
  - Consider creating web endpoint

- [ ] **Test Production Inference**
  - Verify response times
  - Check GPU memory usage
  - Test with various prompts
  - Monitor costs

- [ ] **Document Usage**
  - Note model location on Modal
  - Document inference function
  - Add ethical disclaimers
  - Create usage examples

---

## 📊 Expected Timeline

| Phase | Duration | Notes |
|-------|----------|-------|
| Setup & Auth | 10-15 min | One-time setup |
| Test Setup | 5-10 min | First run builds container |
| Dataset Inspection | 2-5 min | Quick check |
| Test Training | 5-10 min | 5 steps only |
| Full Training | **~10 minutes** ⚡ | **H100 GPU - FAST!** |
| Evaluation | 10-15 min | Testing inference |
| Model Management | 5-10 min | Save/export options |
| **Total** | **~45-60 min** | First time setup (much faster!) |

---

## 💰 Cost Estimate

**Option 1: H100 GPU (FAST - Recommended for Speed)**
- **H100 GPU**: ~$8-10/hour
- **Test Setup**: ~$0.10 (10 minutes)
- **Test Training**: ~$0.10 (10 minutes)
- **Full Training**: **~$1.50-2.00** (10 minutes on H100!)
- **Inference Testing**: ~$0.25 (15 minutes)
- **Total Estimated Cost**: **~$2.00-2.50** for complete fine-tuning
- **Speed**: ⚡ **~10 minutes** for full training!

**Option 2: A10G GPU (Slower but Cheaper)**
- **A10G GPU**: ~$0.75-1.00/hour
- **Full Training**: ~$1.50-2.00 (1-2 hours)
- **Total Estimated Cost**: **~$2.00-2.50** (same cost, but slower)
- **Speed**: 🐌 1-2 hours for full training

**Recommendation**: Use H100 for speed! Same cost, 10x faster!

---

## 🎯 Success Criteria

- [ ] Model trains successfully (loss decreases)
- [ ] Model saves to Modal volume
- [ ] Inference produces appropriate therapeutic responses
- [ ] Responses are empathetic and contextually relevant
- [ ] No technical errors during training or inference
- [ ] Model can be loaded and used for inference

---

## 🚨 Troubleshooting

### Authentication Issues
- **Problem**: `modal setup` fails
- **Solution**: Try again, check internet connection, use different browser

### HF Token Issues
- **Problem**: Can't access dataset
- **Solution**: Verify secret exists: `modal secret list`, recreate if needed

### GPU Out of Memory
- **Problem**: OOM errors during training
- **Solution**: Reduce batch size, use smaller model, or switch to A100

### Training Loss Not Decreasing
- **Problem**: Loss stays high or increases
- **Solution**: Check learning rate, verify dataset formatting, check data quality

### Model Not Saving
- **Problem**: Can't find model in volume
- **Solution**: Check volume path, verify write permissions, check logs

---

## 📝 Notes & Observations

**Document your findings here:**

- Dataset structure: _______________________
- Dataset size: _______________________
- Training time: _______________________
- Final loss: _______________________
- Best hyperparameters: _______________________
- Issues encountered: _______________________
- Solutions found: _______________________

---

## 🔗 Quick Reference Commands

```bash
# Authentication
modal setup

# List secrets
modal secret list

# Run scripts
modal run test_setup.py
modal run train_qwen_therapist_lora.py

# Volume management
modal volume list
modal volume ls training-data
modal volume get training-data /qwen_therapist_lora ./local_model

# Check status
modal app list
modal token current
```

---

## ✅ Final Checklist

Before considering the project complete:

- [ ] Model trained successfully
- [ ] Model saved to Modal volume
- [ ] Inference tested and working
- [ ] Responses are appropriate and empathetic
- [ ] Model documented (location, usage)
- [ ] Ethical disclaimers added (if deploying)
- [ ] Costs reviewed and acceptable
- [ ] Next steps planned (deployment, improvements, etc.)

---

**Ready to start? Begin with Phase 1: Setup & Authentication!**

