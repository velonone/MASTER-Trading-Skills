"""
Adversarial Intelligence Layer — Behavioral & Opponent Modeling
================================================================
Quantifies market-participant behavior to generate counter-party
aware trading signals.

Modules:
- sentiment: FOMO, panic, greed detection
- whale: On-chain whale accumulation / distribution tracking
- intent: Project-team intent inference from unlock schedules
"""

from skills.adversarial.sentiment import FOMODetector
from skills.adversarial.whale import WhaleTracker

__all__ = [
    "FOMODetector",
    "WhaleTracker",
]
