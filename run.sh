#!/bin/bash
set -e

echo "=========================================================="
echo "Starting AI Customer Service & Business Analytics Platform"
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}/backend:${PYTHONPATH}"

echo "[1/2] Verifying Machine Learning Models..."
python3 -m app.ml.train

echo "[2/2] Starting FastAPI Backend on http://localhost:8000 ..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
