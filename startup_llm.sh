#!/usr/bin/env bash
# This script automatically configures the Vast.ai "Thinker" instance.

set -e # Exit immediately if a command fails

echo ">> 1. Installing dependencies..."
pip install ollama redis modelcache sentence-transformers

echo ">> 2. Setting up and starting Ollama..."
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
sleep 5 # Give the server a moment to start up

echo ">> 3. Pulling the LLM model..."
# Updated to qwen3-coder for better coding capabilities
ollama pull qwen3-coder

echo ">> 4. Cloning your application repository..."
# Validate required environment variables
if [ -z "$GIT_REPO" ]; then
  echo "Error: GIT_REPO environment variable is required"
  exit 1
fi

# The GIT_REPO environment variable is passed in by the 'vastai create' command.
git clone "$GIT_REPO" /app
cd /app

echo ">> 5. Launching your Python application..."
# The Redis credentials are also passed in as environment variables.
# Launch the API proxy that bridges Anthropic API to Ollama
python3 api_proxy.py
