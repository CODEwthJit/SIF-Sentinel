#!/usr/bin/env bash
set -e

# Resolve script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "==================================================================="
echo "  SIF Sentinel - Starting Automated Launch (macOS / Linux)"
echo "==================================================================="

# Detect python executable
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo ""
    echo "[ERROR] Python 3 was not found in your PATH."
    echo "Please install Python 3.10 or higher and add it to your PATH."
    echo ""
    exit 1
fi

# Execute the universal launcher
exec "$PYTHON_BIN" run.py

