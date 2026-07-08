#!/bin/bash
# Run all quality checks without modifying files: import order, formatting,
# lint, and the test suite. Intended for local use and CI.
set -e

cd "$(dirname "$0")/.."

echo "Checking import order with isort..."
uv run --extra dev isort --check-only --diff backend main.py

echo "Checking formatting with Black..."
uv run --extra dev black --check --diff backend main.py

echo "Linting with flake8..."
uv run --extra dev flake8 backend main.py

echo "Running tests..."
uv run --extra dev pytest

echo "All checks passed."
