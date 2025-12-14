#!/usr/bin/env python3
"""
Run MindEval benchmark using vLLM server as OpenAI-compatible API.

Usage:
    python scripts/run_mind_eval.py --vllm-url https://your-workspace--vllm-therapist-serve.modal.run

Or set environment variable:
    export VLLM_SERVER_URL=https://your-workspace--vllm-therapist-serve.modal.run
    python scripts/run_mind_eval.py

Or the script will automatically read from .env.local if it exists.
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Add mind_eval_benchmark to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "mind_eval_benchmark"))

from mindeval.scripts.generate_interactions import main as generate_interactions
from mindeval.scripts.generate_judgments import main as generate_judgments
from mindeval.utils import load_jsonl
import pandas as pd


def load_env_local():
    """Load environment variables from .env.local if it exists."""
    env_local_path = project_root / ".env.local"
    if env_local_path.exists():
        with open(env_local_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value


def get_vllm_api_params(vllm_url: str, model_name: str = "qwen-therapist") -> dict:
    """
    Convert vLLM server URL to litellm-compatible API parameters.
    Matches the exact same approach used in app/api/chat/route.ts
    
    The chat route:
    1. Gets OPENAI_API_BASE from env
    2. Ensures it ends with /v1
    3. Uses createOpenAICompatible with baseURL and apiKey
    4. Uses the model name from AI_MODEL
    
    For litellm, we do the same:
    - Use the base URL with /v1
    - Use the model name directly
    - Set api_key to 'not-needed' (same as chat route)
    """
    # Remove trailing slash if present
    vllm_url = vllm_url.rstrip('/')
    
    # Ensure baseURL includes /v1 (same logic as chat route)
    # Chat route: if (!baseURL.endsWith('/v1')) { baseURL = baseURL.endsWith('/') ? `${baseURL}v1` : `${baseURL}/v1`; }
    if not vllm_url.endswith('/v1'):
        if vllm_url.endswith('/'):
            base_url = f"{vllm_url}v1"
        else:
            base_url = f"{vllm_url}/v1"
    else:
        base_url = vllm_url
    
    # litellm format for OpenAI-compatible APIs
    # For custom endpoints, litellm needs 'openai/' prefix to recognize it as OpenAI-compatible
    # But we match the chat route's approach: use base URL with /v1 and model name
    return {
        "model": f"openai/{model_name}",  # litellm needs 'openai/' prefix for custom endpoints
        "api_base": base_url,  # Base URL with /v1 (matches chat route baseURL exactly)
        "api_key": "not-needed",  # Same as chat route
    }


def run_evaluation(
    vllm_url: str,
    output_dir: str = "mind_eval_benchmark/results",
    n_turns: int = 10,
    max_workers: int = 10,
    model_name: str = "qwen-therapist",
):
    """Run the full MindEval evaluation pipeline."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    interactions_path = output_path / "interactions.jsonl"
    judgments_path = output_path / "judgments.jsonl"
    summary_path = output_path / "summary.json"
    
    print("=" * 70)
    print("🧠 Running MindEval Benchmark")
    print("=" * 70)
    print(f"📡 vLLM Server: {vllm_url}")
    print(f"🤖 Model: {model_name}")
    print(f"📊 Output Directory: {output_dir}")
    print()
    
    # Get API params for clinician model (our vLLM model)
    clinician_api_params = get_vllm_api_params(vllm_url, model_name)
    
    # For member model, we'll use a lightweight model or the same vLLM
    # You can change this to use a different model for the patient simulation
    member_api_params = get_vllm_api_params(vllm_url, model_name)
    
    # For judge model, we can use the same vLLM or a different one
    # Using the same vLLM for now, but you might want to use a more capable judge
    judge_api_params = get_vllm_api_params(vllm_url, model_name)
    
    print("Step 1: Generating interactions...")
    print(f"  Clinician API params: {clinician_api_params}")
    print()
    
    # Generate interactions
    generate_interactions(
        profiles_path="mind_eval_benchmark/data/profiles.jsonl",
        clinician_system_template_version="custom",  # or "v0_1" for general-purpose
        clinician_model_api_params=clinician_api_params,
        member_system_template_version="v0_2",
        member_model_api_params=member_api_params,
        n_turns=n_turns,
        max_workers=max_workers,
        output_path=str(interactions_path),
    )
    
    print()
    print("Step 2: Generating judgments...")
    print()
    
    # Generate judgments
    generate_judgments(
        interactions_path=str(interactions_path),
        judge_template_version="v0_1",
        judge_model_api_params=judge_api_params,
        max_workers=max_workers,
        output_path=str(judgments_path),
    )
    
    print()
    print("Step 3: Calculating summary statistics...")
    print()
    
    # Load and analyze results
    full_judgments = load_jsonl(str(judgments_path))
    float_judgments = [j["parsed_judgment"] for j in full_judgments]
    df = pd.DataFrame(float_judgments)
    
    # Calculate summary statistics
    summary = {
        "model": model_name,
        "vllm_url": vllm_url,
        "n_interactions": len(full_judgments),
        "n_turns": n_turns,
        "mean_scores": df.mean().to_dict(),
        "std_scores": df.std().to_dict(),
        "min_scores": df.min().to_dict(),
        "max_scores": df.max().to_dict(),
        "all_scores": float_judgments,
    }
    
    # Save summary
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print("=" * 70)
    print("✅ Evaluation Complete!")
    print("=" * 70)
    print(f"\n📁 Results saved to: {output_dir}")
    print(f"   - Interactions: {interactions_path}")
    print(f"   - Judgments: {judgments_path}")
    print(f"   - Summary: {summary_path}")
    print()
    print("📊 Mean Scores:")
    print(df.mean().to_string())
    print()
    
    return summary


def main():
    # Load .env.local if it exists
    load_env_local()
    
    # Get vLLM URL from various sources (priority: CLI arg > env var > .env.local)
    default_vllm_url = (
        os.getenv("VLLM_SERVER_URL") or 
        os.getenv("OPENAI_API_BASE") or 
        None
    )
    
    # Get model name from various sources
    default_model_name = (
        os.getenv("AI_MODEL") or 
        "qwen-therapist"
    )
    
    parser = argparse.ArgumentParser(description="Run MindEval benchmark with vLLM")
    parser.add_argument(
        "--vllm-url",
        type=str,
        default=default_vllm_url,
        help="vLLM server URL (or set VLLM_SERVER_URL/OPENAI_API_BASE env var, or use .env.local)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=default_model_name,
        help="Model name as served by vLLM (default: from AI_MODEL env var or 'qwen-therapist')",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="mind_eval_benchmark/results",
        help="Output directory for results",
    )
    parser.add_argument(
        "--n-turns",
        type=int,
        default=10,
        help="Number of conversation turns (default: 10)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Max parallel workers (default: 10)",
    )
    
    args = parser.parse_args()
    
    if not args.vllm_url:
        print("❌ Error: vLLM server URL required!")
        print("\nSet it via:")
        print("  --vllm-url https://your-workspace--vllm-therapist-serve.modal.run")
        print("  or")
        print("  export VLLM_SERVER_URL=https://your-workspace--vllm-therapist-serve.modal.run")
        sys.exit(1)
    
    run_evaluation(
        vllm_url=args.vllm_url,
        output_dir=args.output_dir,
        n_turns=args.n_turns,
        max_workers=args.max_workers,
        model_name=args.model_name,
    )


if __name__ == "__main__":
    main()
