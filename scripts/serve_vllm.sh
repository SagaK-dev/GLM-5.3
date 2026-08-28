#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="${MODEL_ID:-zai-org/GLM-5.3}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

exec vllm serve "$MODEL_ID" \
  --host "$HOST" \
  --port "$PORT" \
  "$@"
