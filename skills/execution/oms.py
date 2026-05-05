"""
Order Management System (OMS)
==============================
State machine for order lifecycle tracking, partial-fill handling,
and position reconciliation across multiple connectors.
"""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from skills.core.logging import get_logger
from skills.core.types import ExecutionReport, Order, OrderSide, Position, Signal, SignalAction

_logger = get_logger("execution.oms")


class OrderManagementSystem:
    """
    Lightweight OMS for AI-Agent trading workflows.
    Maintains order book, fill ledger, and position state.
    """

    def __init__(self):
        self.orders: dict[str, Order] = {}
        self.reports: dict[str, list[ExecutionReport]] = {}
        self.positions: dict[str, Position] = {}
        self._lock = asyncio.Lock()

    async def submit(self, order: Order) -> str:
        """Stage an order in the OMS. Returns client order ID."""
        async with self._lock:
            oid = order.id or self._generate_id()
            order.id = oid
            self.orders[oid] = order
            self.reports[oid] = []
            _logger.info(
                "oms.order_submitted id=%s symbol=%s side=%s qty=%s",
                oid,
                order.symbol,
                order.side,
                order.quantity,
            )
            return oid

    async def on_report(self, report: ExecutionReport) -> None:
        """Ingest an execution report from a connector."""
        async with self._lock:
            oid = report.order.id
            if oid not in self.reports:
                self.reports[oid] = []
            self.reports[oid].append(report)
            _logger.info(
                "oms.report id=%s status=%s filled=%s avg_price=%s",
                oid,
                report.status,
                report.total_filled,
                report.avg_fill_price,
            )
            await self._reconcile_position(report)

    async def _reconcile_position(self, report: ExecutionReport) -> None:
        """
        Reconcile a fill against the symbol's running position.

        Sign convention: ``pos.size > 0`` is long, ``< 0`` is short, ``== 0``
        is flat. BUY fills add to size; SELL fills subtract. Realized PnL is
        only accrued on the *closing* portion of a fill — i.e. when the fill
        reduces or flips the existing position. The remainder (if any) opens
        a new exposure on the opposite side, with its own entry price.
        """
        symbol = report.order.symbol
        side = report.order.side
        fill_qty = report.total_filled
        fill_price = report.avg_fill_price or Decimal("0")

        if fill_qty <= 0:
            return

        pos = self.positions.get(symbol)
        if pos is None:
            pos = Position(
                symbol=symbol,
                side="FLAT",
                size=Decimal("0"),
                entry_price=Decimal("0"),
            )

        signed_delta = fill_qty if side == OrderSide.BUY else -fill_qty
        old_size = pos.size
        new_size = old_size + signed_delta

        # Case 1: same-direction add (or opening from flat).
        # No realized PnL; entry price is the weighted average.
        if (
            old_size == 0
            or (old_size > 0 and signed_delta > 0)
            or (old_size < 0 and signed_delta < 0)
        ):
            abs_old = abs(old_size)
            abs_delta = abs(signed_delta)
            new_abs = abs_old + abs_delta
            pos.entry_price = (
                (abs_old * pos.entry_price + abs_delta * fill_price) / new_abs
                if new_abs > 0
                else Decimal("0")
            )
            pos.size = new_size
        else:
            # Case 2: opposite direction. Split into closing + (optional) flip.
            closing_qty = min(abs(old_size), abs(signed_delta))
            if old_size > 0:
                # Closing a long with a sell: profit when fill_price > entry.
                realized = closing_qty * (fill_price - pos.entry_price)
            else:
                # Closing a short with a buy: profit when fill_price < entry.
                realized = closing_qty * (pos.entry_price - fill_price)
            pos.realized_pnl += realized

            if abs(signed_delta) > abs(old_size):
                # Position flipped — remainder opens a new exposure at fill_price.
                pos.entry_price = fill_price
            elif new_size == 0:
                pos.entry_price = Decimal("0")
            # else: partial close, entry_price unchanged.
            pos.size = new_size

        if pos.size > 0:
            pos.side = "LONG"
        elif pos.size < 0:
            pos.side = "SHORT"
        else:
            pos.side = "FLAT"

        self.positions[symbol] = pos

    def position(self, symbol: str) -> Position | None:
        return self.positions.get(symbol)

    def all_positions(self) -> list[Position]:
        return list(self.positions.values())

    def signal_to_order(self, signal: Signal, qty: Decimal, order_type: str = "MARKET") -> Order:
        """Convert a standardized Signal into an OMS Order."""
        side = OrderSide.BUY if signal.action in (SignalAction.BUY,) else OrderSide.SELL
        return Order(
            symbol=signal.symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            metadata={"signal_source": signal.source, "confidence": signal.confidence},
        )

    def _generate_id(self) -> str:
        import uuid

        return f"mt-{uuid.uuid4().hex[:12]}"

    # ------------------------------------------------------------------
    # Persistence (opt-in)
    # ------------------------------------------------------------------

    def to_snapshot(self) -> dict[str, Any]:
        """
        Serialize the OMS state to a JSON-friendly dict.

        Captures orders, execution reports, and positions. Decimals and
        datetimes are stringified via Pydantic's ``model_dump(mode="json")``
        so the snapshot round-trips through :func:`json.dumps`.
        """
        return {
            "orders": {oid: o.model_dump(mode="json") for oid, o in self.orders.items()},
            "reports": {
                oid: [r.model_dump(mode="json") for r in reports]
                for oid, reports in self.reports.items()
            },
            "positions": {sym: p.model_dump(mode="json") for sym, p in self.positions.items()},
        }

    def save(self, path: str | Path) -> None:
        """Persist the OMS state to ``path`` as JSON. Caller picks the format."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_snapshot(), indent=2), encoding="utf-8")

    def load_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Restore the OMS state from a snapshot produced by :meth:`to_snapshot`."""
        self.orders = {oid: Order(**data) for oid, data in snapshot.get("orders", {}).items()}
        self.reports = {
            oid: [ExecutionReport(**r) for r in reports]
            for oid, reports in snapshot.get("reports", {}).items()
        }
        self.positions = {
            sym: Position(**data) for sym, data in snapshot.get("positions", {}).items()
        }

    @classmethod
    def from_file(cls, path: str | Path) -> OrderManagementSystem:
        """
        Construct an OMS pre-loaded from ``path``. If the file does not
        exist, an empty OMS is returned — callers can use this as a
        crash-recovery boot path without having to branch on existence.
        """
        oms = cls()
        target = Path(path)
        if target.exists():
            oms.load_snapshot(json.loads(target.read_text(encoding="utf-8")))
        return oms
