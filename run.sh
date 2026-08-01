#!/usr/bin/env bash
# ============================================================
#  SDG Policy Paper Agent - ONE-COMMAND RUNNER (Mac/Linux)
#  Usage:  bash run.sh
# ============================================================
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Install Python from https://www.python.org/downloads"
    exit 1
fi

[ -d .venv ] || { echo "[1/3] Creating virtual environment..."; python3 -m venv .venv; }

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[2/3] Installing/updating packages - may take a few minutes the first time..."
pip install -q -r requirements.txt

echo "[3/3] Starting the app - opening http://localhost:8501 in your browser..."
streamlit run app.py
