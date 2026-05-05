FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY skills/ ./skills/
COPY backtest/ ./backtest/
COPY tests/ ./tests/
COPY examples/ ./examples/
COPY docs/ ./docs/
COPY README.md CHANGELOG.md LICENSE ./

# Run tests as health check
RUN pytest tests/ -q

CMD ["python", "-c", "from skills.core import registry; print('MASTER Trading Skill Pack ready')"]
