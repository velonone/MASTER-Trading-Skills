# MASTER Trading Development Setup (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "=== MASTER Trading Development Setup ===" -ForegroundColor Cyan

# Check Python version
$pyVersion = python --version 2>&1
if ($pyVersion -notmatch "3\.(1[1-9]|[2-9][0-9])") {
    Write-Error "Python >= 3.11 required (found $pyVersion)"
    exit 1
}

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate
& .venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -e ".[dev,security]"

# Install pre-commit hooks
Write-Host "Installing pre-commit hooks..." -ForegroundColor Yellow
pre-commit install

# Validation
Write-Host "Running validation..." -ForegroundColor Yellow
pytest tests/ -q
mypy skills backtest --ignore-missing-imports
ruff check skills backtest tests

Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host "Run tests: pytest tests/ -v"
Write-Host "Run lint: ruff check skills backtest tests"
