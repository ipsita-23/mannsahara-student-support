#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -x .local/ollama ]]; then
  executable="$PWD/.local/ollama"
else
  executable="$(command -v ollama)"
fi
export OLLAMA_HOST=127.0.0.1:11435
exec "$executable" pull qwen2.5:3b
