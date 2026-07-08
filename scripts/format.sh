#!/bin/bash
# Auto-format the codebase with isort and Black.
set -e

cd "$(dirname "$0")/.."

echo "Sorting imports with isort..."
uv run --extra dev isort backend main.py

echo "Formatting code with Black..."
uv run --extra dev black backend main.py

echo "Done."
