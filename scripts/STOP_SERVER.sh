#!/bin/bash
# Stop the vLLM server on Modal
# Usage: ./STOP_SERVER.sh

cd /Users/noahsark/Documents/vibecoding/finetuningtest
source venv/bin/activate

echo "🛑 Stopping vLLM server..."
modal app stop vllm-therapist

echo ""
echo "✅ Server stopped!"
echo ""
echo "💡 To start it again, run:"
echo "   modal deploy vllm_server.py"

