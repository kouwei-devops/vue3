#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
# 使用仓库自带的虚拟环境（首次运行前先执行：python3 -m venv .venv && .venv/bin/pip install -r python/requirements.txt）
source "$REPO_ROOT/.venv/bin/activate"
cd "$SCRIPT_DIR"
uvicorn main:app --env-file .env.demo --host 127.0.0.1 --port 8000
