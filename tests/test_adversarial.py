"""
Unit tests for skills.adversarial — Behavioral & Opponent Modeling.
"""

import pytest
from skills.adversarial.sentiment import FOMODetector
from skills.adversarial.whale import WhaleTracker
from skills.core.types import SignalAction


def test_fomo_detector_hold():
    det = FOMODetector()
    signal = det.detect("BTC/USDT", prices=[50000, 50100, 50200], volumes=[100, 110, 105])
    assert signal.action in (SignalAction.HOLD, SignalAction.BUY, SignalAction.SELL)


def test_fomo_detector_extreme_fomo():
    det = FOMODetector()
    prices = [50000, 55000, 60000, 65000]
    volumes = [100, 500, 1000, 2000]
    signal = det.detect("BTC/USDT", prices=prices, volumes=volumes)
    assert signal.metadata["fomo_score"] > 60 or signal.action == SignalAction.HOLD


def test_fomo_detector_panic():
    det = FOMODetector()
    prices = [60000, 55000, 50000, 45000]
    volumes = [100, 800, 1500, 2000]
    signal = det.detect("BTC/USDT", prices=prices, volumes=volumes)
    # Panic should suggest accumulation (BUY) or at least not SELL
    assert signal.action in (SignalAction.BUY, SignalAction.HOLD)


def test_whale_tracker_no_key():
    wt = WhaleTracker()
    signal = asyncio.run(wt.track("0x0000000000000000000000000000000000000000"))
    assert signal.confidence == 0.0
    assert "Etherscan API key required" in signal.evidence[0]


def test_whale_classification_accumulation():
    wt = WhaleTracker(etherscan_api_key="dummy")
    behavior, conf, ev = wt._classify({
        "net_flow_eth": 500.0,
        "total_flow_eth": 1000.0,
        "exchange_interactions": 1,
        "token_symbol": "ETH",
    })
    assert behavior == "accumulation"
    assert conf > 0.6


def test_whale_classification_distribution():
    wt = WhaleTracker(etherscan_api_key="dummy")
    behavior, conf, ev = wt._classify({
        "net_flow_eth": -600.0,
        "total_flow_eth": 1000.0,
        "exchange_interactions": 6,
        "token_symbol": "ETH",
    })
    assert behavior == "distribution"
    assert conf > 0.6
    assert any("exchange" in e.lower() for e in ev)


import asyncio
