#!/usr/bin/env bash
set -euo pipefail

echo "=== MASTER Trading Development Setup ==="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED="3.11"

if [ "$(printf '%s\n' "$REQUIRED" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED" ]; then
    echo "Error: Python >= 3.11 required (found $PYTHON_VERSION)"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install in development mode
echo "Installing dependencies..."
pip install -e ".[dev,security]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Run initial validation
echo "Running validation..."
pytest tests/ -q || true
mypy skills backtest --ignore-missing-imports || true
ruff check skills backtest tests || true

echo ""
echo "=== Setup complete! ==="
echo "Activate with: source .venv/bin/activate"
echo "Run tests: make test"
echo "Run lint: make lint"
