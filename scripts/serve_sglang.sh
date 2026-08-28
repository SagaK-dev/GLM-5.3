#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="${MODEL_ID:-zai-org/GLM-5.3}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-30000}"

exec python -m sglang.launch_server \
  --model-path "$MODEL_ID" \
  --host "$HOST" \
  --port "$PORT" \
  "$@"
