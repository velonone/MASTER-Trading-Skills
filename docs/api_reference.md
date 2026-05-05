# API Reference

## Core Types (`skills.core.types`)

### `Signal`
Universal signal emitted by every strategy module.

```python
class Signal(BaseModel):
    action: SignalAction           # BUY, SELL, HOLD, REDUCE, CLOSE, EMERGENCY_LIQUIDATE
    confidence: float              # [0, 1]
    strength: float                # [0, 1] signal intensity
    symbol: str                    # e.g. "BTC/USDT"
    timeframe: Optional[str]       # "1m", "5m", "1h", "4h", "1d"
    source: str                    # Skill name that generated the signal
    primitive: Optional[str]       # Named inference primitive used
    metadata: Dict[str, Any]       # Skill-specific payload
    evidence: List[str]            # Human-readable rationale
    timestamp: datetime
    expiry: Optional[datetime]     # Signal invalidation time
```

### `MarketData`
Normalized market-data snapshot.

```python
class MarketData(BaseModel):
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    quote_volume: Decimal
    trades: int
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    funding_rate: Optional[Decimal]
    open_interest: Optional[Decimal]
```

## Inference Engine (`skills.inference`)

### `HigherOrderInferenceEngine`

```python
engine = HigherOrderInferenceEngine(library: Optional[PrimitiveLibrary] = None)

# Singularity detection
result = engine.detect_singularity(event: dict)
# → {is_singularity: bool, score: float, reasons: list, recommendation: str}

# Causal chain construction
chain = engine.build_causal_chain(event_description: str, category: EventCategory)
# → CausalChain with effects, convergence, overall_confidence

# Full prediction pipeline
prediction = engine.generate_prediction(event_description: str, category: EventCategory)
# → dict with causal_chain, convergence, signal_action, primitive_references

# Self-upgrade diagnostics
diagnostics = engine.diagnostics()
```

### `PrimitiveLibrary`

```python
lib = PrimitiveLibrary.default_library()
lib.add(primitive: InferencePrimitive)
lib.underperformers(min_uses=5, threshold=0.4)
lib.accuracy_report()
```

## Signals (`skills.signals`)

### `OrderBookImbalance`

```python
obi = OrderBookImbalance(levels=5, long_threshold=0.25, short_threshold=-0.25)
signal = obi.generate(symbol="BTC/USDT", bids=[(65000, 5.0)], asks=[(65010, 2.0)])
```

### `FundingArbitrageSignal`

```python
sig = FundingArbitrageSignal(threshold=Decimal("0.0003"))
signal = sig.generate(symbol="BTC/USDT", funding_rate=Decimal("-0.0005"))
```

### `KellyPositionSizer`

```python
kelly = KellyPositionSizer(fraction=0.25, max_position_pct=0.20)
size = kelly.compute(win_rate=0.60, win_loss_ratio=2.0, current_drawdown=0.05)
# → Decimal position size as fraction of capital
```

## Execution (`skills.execution`)

### `CCXTConnector`

```python
conn = CCXTConnector(
    exchange_id="binance",
    api_key="...",
    api_secret="...",
    sandbox=True,
)

# Fetch data
ohlcv = await conn.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=100)

# Place order
report = await conn.place_order(Order(
    symbol="BTC/USDT",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    quantity=Decimal("0.1"),
))
```

### `Web3DEXExecutor`

```python
executor = Web3DEXExecutor(
    rpc_url="https://eth-mainnet.g.alchemy.com/v2/...",
    private_key="0x...",
    mev_protection="flashbots",
)

gas = await executor.get_gas_price()
tx_hash = await executor.send_transaction(tx_dict)
receipt = await executor.await_confirmation(tx_hash, confirmations=2)
```

## Backtest (`backtest`)

### `BacktestEngine`

```python
engine = BacktestEngine(
    data=df_ohlcv,                    # pandas DataFrame
    strategy=my_strategy,             # object with generate(bar) method
    initial_capital=100_000.0,
    commission=0.0004,
    slippage_model=VolatilitySlippage(base_bps=2.0),
)

result = engine.run()
# result.sharpe_ratio, result.max_drawdown, result.total_return
# result.equity_curve, result.trade_log, result.drawdown_series
```

## Agent Adapter (`skills.agent`)

### `AgentToolAdapter`

```python
adapter = AgentToolAdapter(registry)

# Export schemas
openai_tools = adapter.export_openai_tools()
anthropic_tools = adapter.export_anthropic_tools()

# Dispatch LLM tool calls
result = await adapter.dispatch("fomo_detector", {"symbol": "BTC/USDT", "prices": [...]})
```
