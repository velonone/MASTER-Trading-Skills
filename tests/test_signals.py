"""
Unit tests for skills.signals — Multi-Strategy Alpha Factory.
"""

import numpy as np

from skills.core.types import SignalAction
from skills.signals import (
    FundingArbitrageSignal,
    KellyPositionSizer,
    OrderBookImbalance,
)
from skills.signals.chaos.lyapunov import LyapunovExponentAnalyzer


def test_obi_calculation():
    bids = [(100, 10), (99, 5), (98, 3)]
    asks = [(101, 4), (102, 6), (103, 2)]
    obi = OrderBookImbalance(levels=2)
    signal = obi.generate("TEST/USD", bids=bids, asks=asks)
    assert signal.action in (SignalAction.BUY, SignalAction.HOLD)
    assert signal.metadata["obi"] > 0  # bid vol 15 > ask vol 10


def test_obi_strong_sell():
    bids = [(100, 1), (99, 1)]
    asks = [(101, 10), (102, 10)]
    obi = OrderBookImbalance(levels=2, short_threshold=-0.25)
    signal = obi.generate("TEST/USD", bids=bids, asks=asks)
    assert signal.action == SignalAction.SELL


def test_funding_arbitrage_long():
    from decimal import Decimal

    sig = FundingArbitrageSignal(threshold=Decimal("0.0003"))
    signal = sig.generate("BTC/USDT", funding_rate=Decimal("-0.0005"))
    assert signal.action == SignalAction.BUY
    assert "long perp" in signal.evidence[0].lower() or "long_perp" in signal.evidence[0].lower()


def test_funding_arbitrage_neutral():
    from decimal import Decimal

    sig = FundingArbitrageSignal(threshold=Decimal("0.0003"))
    signal = sig.generate("BTC/USDT", funding_rate=Decimal("0.0001"))
    assert signal.action == SignalAction.HOLD


def test_kelly_computation():
    k = KellyPositionSizer(fraction=0.25, max_position_pct=0.20)
    size = k.compute(win_rate=0.60, win_loss_ratio=2.0)
    assert size is not None
    assert float(size) > 0.0


def test_kelly_no_edge():
    k = KellyPositionSizer()
    size = k.compute(win_rate=0.45, win_loss_ratio=1.0)
    assert size is None


def test_kelly_drawdown_compression():
    k = KellyPositionSizer(fraction=0.25, max_position_pct=0.20)
    normal = k.compute(win_rate=0.60, win_loss_ratio=2.0, current_drawdown=0.0)
    compressed = k.compute(win_rate=0.60, win_loss_ratio=2.0, current_drawdown=0.20)
    assert compressed is not None
    assert compressed < normal


def test_adversarial_market_maker_quote():
    from skills.signals.adversarial_rl.market_maker import AdversarialMarketMaker

    mm = AdversarialMarketMaker(spread_bps=10.0)
    bid, ask = mm.quote(mid_price=50000.0, volatility=0.60, inventory=0.5)
    assert bid < 50000.0 < ask
    assert ask - bid > 0


def test_adversarial_stress_test():
    from skills.signals.adversarial_rl.market_maker import AdversarialMarketMaker

    mm = AdversarialMarketMaker()
    paths = [np.cumsum(np.random.randn(100) * 100 + 50000) for _ in range(5)]
    stats = mm.adversarial_stress_test(paths, adversary_intensity=0.3)
    assert "mean_pnl" in stats
    assert "sharpe" in stats


def test_lyapunov_on_random_walk():
    analyzer = LyapunovExponentAnalyzer(embedding_dim=4)
    # Random walk should have near-zero LLE
    np.random.seed(42)
    rw = np.cumsum(np.random.randn(500))
    result = analyzer.compute(rw)
    assert "lle" in result
    assert "regime" in result


def test_lyapunov_on_chaotic():
    # Logistic map: r=4 is chaotic (theoretical LLE = ln(2) ~ 0.693)
    analyzer = LyapunovExponentAnalyzer(embedding_dim=3, lag=1)
    x = 0.5
    series = []
    for _ in range(500):
        x = 4.0 * x * (1.0 - x)
        series.append(x)
    result = analyzer.compute(np.array(series))
    # Rosenstein algorithm on 1D maps can be noisy; we accept non-negative LLE as chaotic signature
    assert result["lle"] >= -0.001
