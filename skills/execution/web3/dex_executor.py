"""
Web3 DEX Executor
==================
Async on-chain execution with MEV protection, gas estimation,
and transaction lifecycle management.

Requires:
    pip install web3>=6.11 eth-account>=0.10
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from skills.core.base import BaseConnector
from skills.core.logging import get_logger
from skills.core.types import ExecutionReport, MarketData, Order, OrderType, Position
from skills.execution.web3.mev_protection import MEVProtection


_logger = get_logger("execution.web3")


class Web3DEXExecutor(BaseConnector):
    """
    Production-grade Web3 executor for DEX swaps and DeFi interactions.
    Implements BaseConnector so it slots into the unified execution seam.
    """

    name = "web3_dex_executor"
    description = "On-chain DEX execution with MEV protection and gas optimization"
    version = "1.0.0"
    venue = "dex"

    def __init__(
        self,
        rpc_url: str,
        private_key: Optional[str] = None,
        mev_protection: Optional[str] = "flashbots",
        chain_id: int = 1,
        allow_stub_swap: bool = False,
    ):
        """
        Args:
            allow_stub_swap: When True, :meth:`swap_exact_in` returns a
                fake tx hash (architecture-only). Production callers must
                leave this False until 1inch / Uniswap router integration
                lands; otherwise the executor would silently report a
                successful swap that never reached the chain.
        """
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.chain_id = chain_id
        self.allow_stub_swap = allow_stub_swap
        self.mev = MEVProtection(provider=mev_protection) if mev_protection else None
        self._web3: Optional[Any] = None

    async def _client(self) -> Any:
        if self._web3 is not None:
            return self._web3
        from web3 import AsyncWeb3, AsyncHTTPProvider
        # Use MEV-protected RPC if configured
        endpoint = self.mev.rpc_url if self.mev else self.rpc_url
        self._web3 = AsyncWeb3(AsyncHTTPProvider(endpoint))
        return self._web3

    async def get_gas_price(self) -> Dict[str, int]:
        """Fetch EIP-1559 gas parameters."""
        w3 = await self._client()
        base_fee = await w3.eth.get_block("latest")
        base_fee_per_gas = base_fee["baseFeePerGas"]
        # Suggest maxFeePerGas at 95th percentile of recent blocks
        max_priority = await w3.eth.max_priority_fee
        max_fee = base_fee_per_gas * 2 + max_priority
        return {
            "base_fee_per_gas": base_fee_per_gas,
            "max_priority_fee_per_gas": max_priority,
            "max_fee_per_gas": max_fee,
        }

    async def send_transaction(self, tx_dict: Dict[str, Any]) -> str:
        """Sign and broadcast a transaction. Returns tx_hash."""
        if not self.private_key:
            raise ValueError("Private key required for transaction signing")
        w3 = await self._client()
        account = w3.eth.account.from_key(self.private_key)
        tx_dict["from"] = account.address
        tx_dict["chainId"] = self.chain_id
        if "nonce" not in tx_dict:
            tx_dict["nonce"] = await w3.eth.get_transaction_count(account.address)
        if "type" not in tx_dict:
            tx_dict["type"] = 2  # EIP-1559
        if "maxFeePerGas" not in tx_dict:
            gas = await self.get_gas_price()
            tx_dict["maxFeePerGas"] = gas["max_fee_per_gas"]
            tx_dict["maxPriorityFeePerGas"] = gas["max_priority_fee_per_gas"]

        signed = account.sign_transaction(tx_dict)
        tx_hash = await w3.eth.send_raw_transaction(signed.rawTransaction)
        hex_hash = tx_hash.hex()
        _logger.info("web3.tx_broadcast chain_id=%s tx_hash=%s", self.chain_id, hex_hash)
        return hex_hash

    async def await_confirmation(self, tx_hash: str, confirmations: int = 2, timeout: int = 120) -> Dict[str, Any]:
        """Wait for transaction receipt with confirmation depth."""
        w3 = await self._client()
        poll_interval = 2.0
        elapsed = 0.0
        while elapsed < timeout:
            try:
                receipt = await w3.eth.get_transaction_receipt(tx_hash)
                if receipt and receipt["blockNumber"]:
                    latest = await w3.eth.get_block_number()
                    if latest - receipt["blockNumber"] >= confirmations:
                        return {
                            "status": "success" if receipt["status"] == 1 else "failed",
                            "block_number": receipt["blockNumber"],
                            "gas_used": receipt["gasUsed"],
                            "confirmations": confirmations,
                            "receipt": dict(receipt),
                        }
            except Exception:
                pass
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        return {"status": "timeout", "tx_hash": tx_hash}

    async def swap_exact_in(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        min_amount_out: Decimal,
        recipient: Optional[str] = None,
        deadline_seconds: int = 300,
    ) -> str:
        """
        Execute a token swap via DEX aggregator (1inch API skeleton).
        In production, integrate 1inch Swap API or Uniswap V4 router.

        Raises:
            NotImplementedError: when ``allow_stub_swap`` is False (default).
                The default raise prevents callers from silently treating a
                fake tx hash as a real fill.
        """
        if not self.allow_stub_swap:
            raise NotImplementedError(
                "swap_exact_in is a placeholder pending 1inch/Uniswap router "
                "integration. Set allow_stub_swap=True on the executor to "
                "exercise the architecture seam (returns a fake tx hash)."
            )
        import uuid
        return f"0x{uuid.uuid4().hex}"

    async def get_balance(self, token_address: Optional[str] = None) -> Decimal:
        """Get ETH or ERC-20 balance."""
        w3 = await self._client()
        if not self.private_key:
            return Decimal("0")
        from eth_account import Account
        account = Account.from_key(self.private_key)
        if token_address is None:
            bal = await w3.eth.get_balance(account.address)
            return Decimal(w3.from_wei(bal, "ether"))
        # ERC-20 balanceOf
        abi = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"}]
        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=abi)
        bal = await contract.functions.balanceOf(account.address).call()
        return Decimal(bal) / Decimal(10 ** 18)

    # ------------------------------------------------------------------
    # BaseConnector interface (unified execution seam)
    # ------------------------------------------------------------------

    async def run(self, context: Dict[str, Any]) -> Any:
        """Agent dispatch entrypoint."""
        action = context.get("action")
        if action == "swap":
            return await self.swap_exact_in(
                token_in=context["token_in"],
                token_out=context["token_out"],
                amount_in=Decimal(str(context["amount_in"])),
                min_amount_out=Decimal(str(context.get("min_amount_out", "0"))),
                recipient=context.get("recipient"),
                deadline_seconds=context.get("deadline_seconds", 300),
            )
        elif action == "balance":
            return await self.get_balance(context.get("token_address"))
        elif action == "gas":
            return await self.get_gas_price()
        elif action == "place_order":
            order = Order(**context["order"])
            return await self.place_order(order)
        elif action == "cancel_order":
            return await self.cancel_order(context["order_id"], context.get("symbol", ""))
        elif action == "position":
            return await self.fetch_position(context.get("symbol", ""))
        else:
            raise ValueError(f"Unknown action: {action}")

    async def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[MarketData]:
        """DEX does not natively provide OHLCV; return empty list."""
        return []

    async def place_order(self, order: Order) -> ExecutionReport:
        """Map a standardized Order to a DEX swap."""
        if order.order_type != OrderType.MARKET:
            return ExecutionReport(
                order=order,
                status="REJECTED",
                total_filled=Decimal("0"),
                remaining=order.quantity,
            )

        token_in = order.metadata.get("token_in")
        token_out = order.metadata.get("token_out")
        if not token_in or not token_out:
            return ExecutionReport(
                order=order,
                status="REJECTED",
                total_filled=Decimal("0"),
                remaining=order.quantity,
            )

        tx_hash = await self.swap_exact_in(
            token_in=token_in,
            token_out=token_out,
            amount_in=order.quantity,
            min_amount_out=order.metadata.get("min_amount_out", Decimal("0")),
            recipient=order.metadata.get("recipient"),
        )

        return ExecutionReport(
            order=order,
            status="PENDING",
            total_filled=Decimal("0"),
            remaining=order.quantity,
        )

    async def cancel_order(self, order_id: str, symbol: str) -> ExecutionReport:
        """DEX transactions cannot be cancelled once broadcast."""
        dummy_order = Order(symbol=symbol, side="BUY", order_type="MARKET", quantity=Decimal("0"))
        return ExecutionReport(
            order=dummy_order,
            status="REJECTED",
            total_filled=Decimal("0"),
            remaining=Decimal("0"),
        )

    async def fetch_position(self, symbol: str) -> Optional[Position]:
        """Return token balance as a Position (LONG if holding)."""
        if not self.private_key:
            return None
        base = symbol.split("/")[0] if "/" in symbol else symbol
        # Native ETH when base == "ETH"; otherwise would need token address mapping
        token_address = None if base.upper() == "ETH" else None
        bal = await self.get_balance(token_address)
        if bal > 0:
            return Position(
                symbol=symbol,
                side="LONG",
                size=bal,
                entry_price=Decimal("0"),
                unrealized_pnl=Decimal("0"),
            )
        return None
