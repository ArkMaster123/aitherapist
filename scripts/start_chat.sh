#!/bin/bash
# Quick start command for vLLM chat
# Usage: ./START_CHAT.sh

cd /Users/noahsark/Documents/vibecoding/finetuningtest
source venv/bin/activate
export VLLM_SERVER_URL=https://whataidea--vllm-therapist-serve.modal.run
python3 chat_vllm.py
