#!/usr/bin/env bash
set -euo pipefail

# Load env if exists
ENV_FILE_DIR="$(cd "$(dirname "$0")"/.. && pwd)/.env"
if [ -f "$ENV_FILE_DIR/.env.local" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE_DIR/.env.local"
  set +a
elif [ -f "$ENV_FILE_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE_DIR/.env"
  set +a
else
  echo "[dev.sh] 未找到环境文件: $ENV_FILE_DIR/.env.local 或 $ENV_FILE_DIR/.env"
  echo "请先创建并填写凭证: cp $ENV_FILE_DIR/.env.example $ENV_FILE_DIR/.env.local"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")"/.. && pwd)"
export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"

echo "Starting services..."

# Prefer venv python if available
PYBIN="python3"
if [ -x "$REPO_ROOT/.venv/bin/python" ]; then
  PYBIN="$REPO_ROOT/.venv/bin/python"
fi

# Portal :9000
$PYBIN -m uvicorn portal.src.main:app --host 0.0.0.0 --port 9000 --reload &
PID_PORTAL=$!

# App1 :9001
$PYBIN -m uvicorn app1.src.main:app --host 0.0.0.0 --port 9001 --reload &
PID_APP1=$!

# App2 :9002
$PYBIN -m uvicorn app2.src.main:app --host 0.0.0.0 --port 9002 --reload &
PID_APP2=$!

trap 'echo Stopping...; kill $PID_PORTAL $PID_APP1 $PID_APP2 2>/dev/null || true' INT TERM
wait

