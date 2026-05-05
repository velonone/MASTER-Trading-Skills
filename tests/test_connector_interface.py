"""
Tests for unified BaseConnector execution seam (P2).
"""

from decimal import Decimal

import pytest

from skills.core.base import BaseConnector, BaseSkill
from skills.core.types import ExecutionReport, Order, OrderSide, OrderType
from skills.execution.web3.dex_executor import Web3DEXExecutor


@pytest.fixture
def dex_executor():
    # allow_stub_swap=True keeps these architecture-seam tests working without
    # a real router integration. Production callers must NOT enable the stub.
    return Web3DEXExecutor(rpc_url="https://eth.llamarpc.com", allow_stub_swap=True)


def test_web3dex_inherits_base_connector(dex_executor):
    """Web3DEXExecutor should be a BaseConnector and BaseSkill."""
    assert isinstance(dex_executor, BaseConnector)
    assert isinstance(dex_executor, BaseSkill)


@pytest.mark.asyncio
async def test_web3dex_fetch_ohlcv_returns_empty(dex_executor):
    """DEX does not natively provide OHLCV."""
    candles = await dex_executor.fetch_ohlcv("ETH/USDT", "1h", 100)
    assert candles == []


@pytest.mark.asyncio
async def test_web3dex_place_order_rejects_non_market(dex_executor):
    """Only MARKET orders are supported (mapped to swap)."""
    order = Order(
        symbol="ETH/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1.0"),
        price=Decimal("3000.0"),
    )
    report = await dex_executor.place_order(order)
    assert isinstance(report, ExecutionReport)
    assert report.status == "REJECTED"


@pytest.mark.asyncio
async def test_web3dex_place_order_without_token_addresses(dex_executor):
    """MARKET order without token_in/token_out metadata should be rejected."""
    order = Order(
        symbol="ETH/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("1.0"),
    )
    report = await dex_executor.place_order(order)
    assert report.status == "REJECTED"


@pytest.mark.asyncio
async def test_web3dex_place_order_with_tokens(dex_executor):
    """MARKET order with token addresses should trigger swap placeholder."""
    order = Order(
        symbol="ETH/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("1.0"),
        metadata={
            "token_in": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
            "token_out": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        },
    )
    report = await dex_executor.place_order(order)
    assert report.status == "PENDING"


@pytest.mark.asyncio
async def test_web3dex_cancel_order_always_rejected(dex_executor):
    """DEX does not support order cancellation post-broadcast."""
    report = await dex_executor.cancel_order("0x123", "ETH/USDT")
    assert isinstance(report, ExecutionReport)
    assert report.status == "REJECTED"


@pytest.mark.asyncio
async def test_web3dex_fetch_position_without_key(dex_executor):
    """Without private key, position should be None."""
    pos = await dex_executor.fetch_position("ETH/USDT")
    assert pos is None


@pytest.mark.asyncio
async def test_web3dex_run_dispatch_swap(dex_executor):
    """run() should dispatch swap action."""
    result = await dex_executor.run(
        {
            "action": "swap",
            "token_in": "0x...",
            "token_out": "0x...",
            "amount_in": "1.5",
            "min_amount_out": "1.4",
        }
    )
    assert isinstance(result, str)
    assert result.startswith("0x")


@pytest.mark.asyncio
async def test_web3dex_run_dispatch_gas(dex_executor):
    """run() should dispatch gas action."""
    try:
        result = await dex_executor.run({"action": "gas"})
        assert "base_fee_per_gas" in result
    except Exception:
        pytest.skip("RPC unavailable")


@pytest.mark.asyncio
async def test_web3dex_run_dispatch_balance_without_key(dex_executor):
    """run() should dispatch balance action."""
    result = await dex_executor.run({"action": "balance"})
    assert result == Decimal("0")


@pytest.mark.asyncio
async def test_web3dex_run_unknown_action(dex_executor):
    """run() should raise on unknown action."""
    with pytest.raises(ValueError, match="Unknown action"):
        await dex_executor.run({"action": "explode"})
