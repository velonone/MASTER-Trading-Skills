"""
MASTER Trading Skills — Runtime Package
========================================
Controlled exports to prevent accidental loading of heavy submodules.

Usage:
    from skills import inference, signals, execution, adversarial, agent
    from skills.core import registry, Signal
"""

# Explicitly list what 'from skills import *' brings in.
# Heavy submodules are NOT auto-imported to save agent context tokens.
__all__ = [
    "core",
    "inference",
    "signals",
    "execution",
    "adversarial",
    "agent",
]
