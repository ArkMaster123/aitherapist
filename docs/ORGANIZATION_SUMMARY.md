# Documentation Organization Summary

All documentation has been organized into logical subfolders within `/docs/`.

## 📂 Organization Structure

```
docs/
├── avatar/                    # Hedra realtime avatar documentation
│   ├── HEDRA_OPTIONS.md
│   ├── HEDRA_QUICK_REFERENCE.md
│   └── HEDRA_REALTIME_AVATAR_SETUP.md
│
├── architecture/              # System architecture and technical docs
│   ├── MODEL_INFO.md
│   ├── STREAMING_GUIDE.md
│   ├── monitoring-and-storage-guide.md
│   └── speed-optimizations.md
│
├── evaluation/                # Model evaluation and testing
│   ├── EVALUATION_REPORT_TEMPLATE.md
│   ├── EVALUATION_SUMMARY.md
│   ├── MINDEVAL_SETUP.md
│   └── RUN_EVALUATION.md
│
├── modal-backend/             # Modal backend services
│   ├── ARCHITECTURE.md
│   ├── CORRECT_ARCHITECTURE.md
│   ├── GROQ_SETUP.md
│   ├── GROQ_VS_PLAN_COMPARISON.md
│   ├── INTEGRATED_PIPELINE_PLAN.md
│   ├── MOSHI_TROUBLESHOOTING.md
│   ├── README.md
│   ├── REVISED_ULTRA_FAST_PLAN.md
│   ├── TTS_SERVICES.md
│   ├── ULTRA_FAST_DEPLOY.md
│   ├── ULTRA_FAST_PIPELINE.md
│   ├── ULTRA_FAST_SETUP.md
│   └── VIBEVOICE_README.md
│
├── setup/                     # Setup and installation guides
│   ├── PUBLISH_GUIDE.md
│   ├── QUICK_START.md
│   ├── QUICK_START_VLLM.md
│   ├── README_SPACE.md
│   ├── SERVER_MANAGEMENT.md
│   ├── SPACE_README.md
│   ├── VLLM_SETUP.md
│   └── WHY_LITE.md
│
├── training/                  # Model training and fine-tuning
│   ├── fine-tuning-guide-modal.md
│   └── lora-training-plan.md
│
└── usage/                     # User guides and how-to docs
    ├── CHATBOT_USAGE.md
    ├── ETHICAL_GUIDELINES.md
    ├── FUNCTION_CALLING_GUIDE.md
    ├── QUICK_REFERENCE.md
    ├── README_CHAT.md
    └── TOOL_CALLING_DEBUG.md
```

## 📋 File Movements

### From `modal-backend/` → `docs/modal-backend/`
- All `.md` files from `modal-backend/` directory

### Hedra Avatar Docs → `docs/avatar/`
- `HEDRA_OPTIONS.md`
- `HEDRA_QUICK_REFERENCE.md`
- `HEDRA_REALTIME_AVATAR_SETUP.md`

### From `docs/` root → Organized folders
- Training docs → `docs/training/`
- Evaluation docs → `docs/evaluation/`
- Usage docs → `docs/usage/`
- Setup docs → `docs/setup/`
- Architecture docs → `docs/architecture/`

## 📍 Files That Stay in Root

These files remain in the project root as they are entry points:
- `README.md` - Main project README
- `CONFIG.md` - Configuration guide
- `DEPLOYMENT.md` - Deployment instructions
- `QUICK_START.md` - Quick start (if exists in root)

## 🔄 Breaking Changes

If you have any hardcoded paths to these files in:
- Code comments
- Configuration files
- Other documentation
- CI/CD scripts

You'll need to update them to the new paths.

## 📝 Next Steps

1. Update any references to old file paths
2. Update links in README files that point to moved documents
3. Consider creating symlinks if needed for backwards compatibility

## 🗂️ Finding Documentation

Use `docs/README.md` as the main index for all documentation.

