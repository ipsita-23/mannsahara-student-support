#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -x .local/ollama ]]; then
  executable="$PWD/.local/ollama"
elif command -v ollama >/dev/null 2>&1; then
  executable="$(command -v ollama)"
else
  echo "Install Ollama from https://ollama.com/download, then rerun this script." >&2
  exit 1
fi
mkdir -p .local/models
export OLLAMA_HOST=127.0.0.1:11435
export OLLAMA_MODELS="$PWD/.local/models"
export OLLAMA_NO_CLOUD=1
export OLLAMA_DEBUG_LOG_REQUESTS=false
exec "$executable" serve
