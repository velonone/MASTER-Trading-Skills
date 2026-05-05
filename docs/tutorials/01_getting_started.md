# Tutorial 1: Getting Started

This tutorial walks you through installing MASTER Trading and running your first inference and signal generation.

## Installation

```bash
git clone https://github.com/velonone/MASTER-Trading-Skills.git
cd MASTER-Trading-Skills
pip install -e ".[dev]"
```

## Your First Prediction

```python
from skills.inference import HigherOrderInferenceEngine
from skills.core.types import EventCategory

engine = HigherOrderInferenceEngine()

prediction = engine.generate_prediction(
    "Coinbase announces listing of new L2 token",
    EventCategory.LISTING
)

print(prediction["signal_action"])       # BUY
print(prediction["overall_confidence"])  # e.g. 0.513
print(prediction["convergence"])         # bullish_convergence
```

## Your First Signal

```python
from skills.signals import OrderBookImbalance

obi = OrderBookImbalance(levels=5)
signal = obi.generate(
    symbol="ETH/USDT",
    bids=[(3500, 10), (3499, 5)],
    asks=[(3501, 2), (3502, 8)],
)

print(signal.action)       # BUY
print(signal.confidence)   # 0.875
print(signal.evidence)     # ["OBI=+0.3125 at top-5 levels"]
```

## Next Steps

- [Tutorial 2: Backtesting a Strategy](02_backtesting.md)
- [Tutorial 3: Web3 Execution](03_web3_execution.md)
- [Tutorial 4: LLM Agent Integration](04_llm_agent.md)
