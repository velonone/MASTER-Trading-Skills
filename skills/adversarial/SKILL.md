---
name: adversarial
version: "2.0.0"
description: Adversarial intelligence — behavioral detection, whale tracking, sentiment analysis
author: VelonLabs
skills:
  - name: fomo_detector
    class: FOMODetector
    module: skills.adversarial.sentiment
    description: Fear-Of-Missing-Out and panic regime detection
    triggers: [fomo, panic, greed, sentiment, behavioral]
  - name: whale_tracker
    class: WhaleTracker
    module: skills.adversarial.whale
    description: On-chain whale transaction classification
    triggers: [whale, onchain, accumulation, distribution]
dependencies: []
---

# Adversarial Intelligence

## FOMODetector

Detects FOMO and panic regimes from price/volume dynamics.

```python
from skills.adversarial.sentiment import FOMODetector

fomo = FOMODetector()
result = fomo.detect(
    symbol="BTC/USDT",
    prices=[50000, 52000, 55000, 58000],
    volumes=[100, 500, 2000, 8000],
)
```

## WhaleTracker

Classifies whale transactions as accumulation, distribution, or neutral.

```python
from skills.adversarial.whale import WhaleTracker

whale = WhaleTracker(etherscan_api_key="your_key")
cls = whale.classify_whale_transaction(
    from_addr="0x...",
    to_addr="0x...",
    value_eth=1500.0,
)
```
