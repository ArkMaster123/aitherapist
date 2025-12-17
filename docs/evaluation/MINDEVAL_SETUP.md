# MindEval Benchmark Setup

This guide explains how to run the MindEval benchmark using your vLLM server.

## Overview

MindEval is a benchmark for evaluating language models on multi-turn mental health support conversations. It tests:
- Therapeutic conversation quality
- Empathy and supportiveness
- Appropriate boundaries
- Crisis handling

## Prerequisites

1. **vLLM Server Running**: Your vLLM server must be deployed and accessible
2. **Python Environment**: Activate your virtual environment with mind-eval dependencies

## Setup

### 1. Install Dependencies

The mind-eval benchmark uses Poetry. Make sure dependencies are installed:

```bash
cd mind_eval_benchmark
poetry install
```

Or if using a virtual environment:

```bash
cd mind_eval_benchmark
pip install -r requirements.txt  # if available
# Or install manually: litellm, pandas, jsonargparse, etc.
```

### 2. Get Your vLLM Server URL

After deploying your vLLM server:

```bash
modal deploy scripts/vllm_server.py
```

You'll get a URL like:
```
https://your-workspace--vllm-therapist-serve.modal.run
```

### 3. Run the Evaluation

```bash
# Set the vLLM server URL
export VLLM_SERVER_URL=https://your-workspace--vllm-therapist-serve.modal.run

# Run the evaluation
python scripts/run_mind_eval.py
```

Or specify the URL directly:

```bash
python scripts/run_mind_eval.py --vllm-url https://your-workspace--vllm-therapist-serve.modal.run
```

### 4. View Results

After the evaluation completes, view results at:
- **Web UI**: http://localhost:3000/evals (or your deployed URL)
- **JSON Summary**: `mind_eval_benchmark/results/summary.json`
- **Raw Data**: 
  - `mind_eval_benchmark/results/interactions.jsonl`
  - `mind_eval_benchmark/results/judgments.jsonl`

## Options

```bash
python scripts/run_mind_eval.py \
  --vllm-url https://your-workspace--vllm-therapist-serve.modal.run \
  --model-name qwen-therapist \
  --output-dir mind_eval_benchmark/results \
  --n-turns 10 \
  --max-workers 10
```

- `--vllm-url`: vLLM server URL (or set `VLLM_SERVER_URL` env var)
- `--model-name`: Model name as served by vLLM (default: `qwen-therapist`)
- `--output-dir`: Output directory for results (default: `mind_eval_benchmark/results`)
- `--n-turns`: Number of conversation turns per interaction (default: 10)
- `--max-workers`: Max parallel workers (default: 10, adjust based on rate limits)

## Understanding Results

The evaluation generates several metrics:

- **Mean Scores**: Average performance across all interactions
- **Standard Deviation**: Variability in performance
- **Min/Max Scores**: Range of performance

Key metrics include:
- Therapeutic quality
- Empathy
- Appropriate responses
- Crisis handling
- Boundary maintenance

## Troubleshooting

### "No evaluation results found"

Make sure you've run the evaluation script first. The web page at `/evals` reads from `mind_eval_benchmark/results/summary.json`.

### "Connection refused" or API errors

1. Check that your vLLM server is running:
   ```bash
   modal app list
   modal app start vllm-therapist  # if not running
   ```

2. Verify the server URL is correct:
   ```bash
   curl https://your-workspace--vllm-therapist-serve.modal.run/health
   ```

3. Check server logs:
   ```bash
   modal app logs vllm-therapist
   ```

### Rate limiting

If you see rate limit errors, reduce `--max-workers`:

```bash
python scripts/run_mind_eval.py --max-workers 5
```

### Model name mismatch

If you get "model not found" errors, check what model name your vLLM server is using:

```bash
curl https://your-workspace--vllm-therapist-serve.modal.run/v1/models
```

Then use that model name with `--model-name`.

## Next Steps

- Compare results across different model versions
- Analyze specific interaction patterns
- Use results to guide further fine-tuning
- Share results with the research community

## References

- [MindEval Paper](https://arxiv.org/abs/2511.18491)
- [MindEval GitHub](https://github.com/SWORDHealth/mind-eval)
