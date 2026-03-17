#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv-backend"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${REPO_ROOT}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python not found: ${PYTHON_BIN}"
  exit 1
fi

if [ ! -d "${VENV_DIR}" ]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m playwright install chromium

export BYEGPT_STORAGE="${REPO_ROOT}/.byegpt"
export BYEGPT_DEMO_MODE="false"
export CORS_ORIGINS="http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:3000,http://localhost:3000"

echo "Host backend starting on http://127.0.0.1:8000"
echo "Next step: open http://127.0.0.1:8000/docs or POST /auth/login to create .byegpt/storage.json"

python scripts/run_host_backend.py
