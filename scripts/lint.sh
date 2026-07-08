#!/bin/bash
# Lint the codebase with flake8.
set -e

cd "$(dirname "$0")/.."

echo "Linting with flake8..."
uv run --extra dev flake8 backend main.py
