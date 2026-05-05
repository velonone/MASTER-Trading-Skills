"""
Structured Logging Setup
========================
Tries structlog first; falls back to stdlib logging if unavailable.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

try:
    import structlog

    _HAS_STRUCTLOG = True
except ImportError:  # pragma: no cover
    _HAS_STRUCTLOG = False


def _configure_stdlib_json() -> None:
    """Configure stdlib logging with JSON-ish formatter for audit trails."""
    handler = logging.StreamHandler(sys.stdout)
    fmt = (
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": %(message)s}'
    )
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S"))
    root = logging.getLogger("master")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _configure_structlog() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def configure_logging() -> None:
    if _HAS_STRUCTLOG:
        _configure_structlog()
    else:
        _configure_stdlib_json()


def get_logger(name: str) -> Any:
    """Return a logger bound with *name*."""
    if _HAS_STRUCTLOG:
        return structlog.get_logger("master." + name)
    return logging.getLogger("master." + name)
