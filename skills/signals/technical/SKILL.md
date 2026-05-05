---
name: signals_technical
version: "2.0.0"
description: Technical signal generators — OBI, Funding Arbitrage, Kelly Criterion
author: VelonLabs
skills:
  - name: order_book_imbalance
    class: OrderBookImbalance
    module: skills.signals.technical.obi
    description: Order Book Imbalance microstructure signal
    triggers: [order_book, obi, depth, microstructure]
  - name: funding_arbitrage
    class: FundingArbitrageSignal
    module: skills.signals.technical.funding_arb
    description: Perpetual funding-rate arbitrage signal
    triggers: [funding, perpetual, basis, arbitrage]
  - name: kelly_criterion
    class: KellyCriterion
    module: skills.signals.technical.kelly
    description: Kelly-optimal position sizing
    triggers: [sizing, kelly, risk]
dependencies: []
---

# Technical Signals

## OrderBookImbalance

Generates BUY/SELL/HOLD signals from order-book depth imbalance.

```python
from skills.signals.technical.obi import OrderBookImbalance

obi = OrderBookImbalance(levels=5, long_threshold=0.25)
signal = obi.generate("BTC/USDT", bids=[[65000, 5.0]], asks=[[65010, 1.5]])
```

## FundingArbitrageSignal

Generates arbitrage signals from perpetual funding rates.

```python
from skills.signals.technical.funding_arb import FundingArbitrageSignal

fa = FundingArbitrageSignal(threshold=Decimal("0.0003"))
signal = fa.generate("BTC/USDT", funding_rate=Decimal("0.0005"))
```
