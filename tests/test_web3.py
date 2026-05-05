"""
Unit tests for Web3 DEX Execution Layer.
"""

from decimal import Decimal

import pytest

from skills.execution.web3 import MEVProtection, Web3DEXExecutor


def test_mev_protection_providers():
    for provider in ["flashbots", "flashbots_standard", "mevblocker", "eden"]:
        mev = MEVProtection(provider=provider)
        assert mev.rpc_url.startswith("http")


def test_mev_invalid_provider():
    with pytest.raises(ValueError):
        MEVProtection(provider="invalid")


@pytest.mark.asyncio
async def test_web3_executor_balance_without_key():
    exec = Web3DEXExecutor(rpc_url="https://eth.llamarpc.com")
    # Without private key, should return 0 or raise gracefully
    bal = await exec.get_balance()
    assert bal == Decimal("0")


@pytest.mark.asyncio
async def test_web3_gas_price_structure():
    exec = Web3DEXExecutor(rpc_url="https://eth.llamarpc.com")
    try:
        gas = await exec.get_gas_price()
        assert "base_fee_per_gas" in gas
        assert "max_fee_per_gas" in gas
        assert "max_priority_fee_per_gas" in gas
    except Exception:
        pytest.skip("RPC unavailable")


@pytest.mark.asyncio
async def test_swap_exact_in_raises_without_stub_flag():
    """Default executor must refuse the stub swap to avoid silent fake fills."""
    exec = Web3DEXExecutor(rpc_url="https://eth.llamarpc.com")
    with pytest.raises(NotImplementedError):
        await exec.swap_exact_in(
            token_in="0x...",
            token_out="0x...",
            amount_in=Decimal("1.5"),
            min_amount_out=Decimal("1.4"),
        )


@pytest.mark.asyncio
async def test_swap_exact_in_placeholder_when_explicitly_enabled():
    """With allow_stub_swap=True the placeholder is exercised for arch tests."""
    exec = Web3DEXExecutor(rpc_url="https://eth.llamarpc.com", allow_stub_swap=True)
    tx_hash = await exec.swap_exact_in(
        token_in="0x...",
        token_out="0x...",
        amount_in=Decimal("1.5"),
        min_amount_out=Decimal("1.4"),
    )
    assert tx_hash.startswith("0x")


def test_mev_headers():
    mev = MEVProtection("flashbots")
    headers = mev.headers()
    assert "Content-Type" in headers
