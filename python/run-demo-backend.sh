#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source /root/vue3/.venv/bin/activate
cd "$SCRIPT_DIR"
uvicorn main:app --env-file .env.demo --host 127.0.0.1 --port 8000
