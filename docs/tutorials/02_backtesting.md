# Tutorial 2: Backtesting a Strategy

Learn how to validate a trading strategy using the vectorized backtest engine.

## Creating a Simple Strategy

```python
from skills.core.types import Signal, SignalAction

class SimpleMomentumStrategy:
    name = "simple_momentum"
    
    def generate(self, bar: dict) -> list:
        if bar["close"] > bar["open"]:
            return [Signal(
                action=SignalAction.BUY,
                confidence=0.7,
                strength=0.5,
                symbol="BTC/USDT",
                source=self.name,
            )]
        return []
```

## Running the Backtest

```python
import pandas as pd
from backtest import BacktestEngine

# Load data
df = pd.read_csv("btc_1h.csv", index_col=0, parse_dates=True)

# Run backtest
engine = BacktestEngine(
    data=df,
    strategy=SimpleMomentumStrategy(),
    initial_capital=100_000,
    commission=0.0004,
)

result = engine.run()

print(f"Sharpe Ratio: {result.sharpe_ratio}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Total Return: {result.total_return:.2%}")
print(f"Win Rate: {result.win_rate:.2%}")
print(f"Number of Trades: {result.trades}")
```

## Analyzing the Equity Curve

```python
import matplotlib.pyplot as plt

result.equity_curve.plot(title="Equity Curve")
plt.axhline(y=100_000, color="r", linestyle="--", label="Initial Capital")
plt.legend()
plt.show()

result.drawdown_series.plot(title="Drawdown")
plt.show()
```

## Adding Slippage

```python
from backtest import VolatilitySlippage

engine = BacktestEngine(
    data=df,
    strategy=SimpleMomentumStrategy(),
    initial_capital=100_000,
    commission=0.0004,
    slippage_model=VolatilitySlippage(base_bps=3.0, volatility_factor=8.0),
)
```

## Best Practices

1. Always backtest before live trading
2. Use realistic slippage and commission assumptions
3. Check out-of-sample performance
4. Validate with multiple market regimes (bull, bear, sideways)
