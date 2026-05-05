.PHONY: install install-dev test test-cov lint format type-check clean docs serve-docs docker-build

PYTHON := python
PIP := pip

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev,security]"
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=skills --cov=backtest --cov-report=term-missing --cov-report=html

lint:
	ruff check skills backtest tests examples
	black --check skills backtest tests examples

format:
	ruff check --fix skills backtest tests examples
	black skills backtest tests examples

type-check:
	mypy skills backtest --ignore-missing-imports

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .mypy_cache build dist *.egg-info

docs:
	cd docs && mkdocs build

serve-docs:
	cd docs && mkdocs serve

docker-build:
	docker build -t master-trading:latest .

docker-run:
	docker run --rm -it master-trading:latest
