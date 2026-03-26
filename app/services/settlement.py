"""
Settlement Workflow Engine — drives transfers through the state machine.

Each step validates the current status, performs the action, records
a settlement event, posts ledger entries, and advances the status.
"""

from datetime import datetime, timezone
from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tables import Transfer, SettlementEvent, Benchmark
from app.models.enums import TransferStatus, VALID_TRANSITIONS
from app.blockchain.simulator import simulate_usdc_transfer, simulate_confirmation
from app.ledger.service import (
    post_funding,
    post_fee_capture,
    post_treasury_allocation,
    post_payout_liability,
    post_settlement_completion,
)
from app.comparison.engine import calculate_comparison


class InvalidTransition(Exception):
    pass


def _validate_transition(current: str, target: TransferStatus):
    current_enum = TransferStatus(current)
    if target not in VALID_TRANSITIONS.get(current_enum, []):
        raise InvalidTransition(f"Cannot move from {current} to {target.value}")


async def _emit_event(db: AsyncSession, transfer_id: str, event_type: str, payload: Optional[Dict] = None):
    event = SettlementEvent(
        transfer_id=transfer_id,
        event_type=event_type,
        payload_json=payload,
    )
    db.add(event)


async def _update_status(db: AsyncSession, transfer: Transfer, new_status: TransferStatus):
    _validate_transition(transfer.status, new_status)
    transfer.status = new_status.value
    transfer.updated_at = datetime.now(timezone.utc)


async def fund_transfer(db: AsyncSession, transfer: Transfer):
    """Mark the transfer as funded and post ledger entries."""
    _validate_transition(transfer.status, TransferStatus.FUNDED)
    await post_funding(db, transfer)
    await post_fee_capture(db, transfer)
    await _update_status(db, transfer, TransferStatus.FUNDED)
    await _emit_event(db, transfer.id, "transfer.funded", {"amount_usd": transfer.source_amount})


async def convert_usd_to_usdc(db: AsyncSession, transfer: Transfer):
    """Simulate treasury USD→USDC conversion."""
    _validate_transition(transfer.status, TransferStatus.USD_TO_USDC_COMPLETE)
    await post_treasury_allocation(db, transfer)
    await _update_status(db, transfer, TransferStatus.USD_TO_USDC_COMPLETE)
    await _emit_event(db, transfer.id, "treasury.usd_to_usdc.completed")


async def submit_onchain_transfer(db: AsyncSession, transfer: Transfer):
    """Simulate submitting a USDC transfer onchain."""
    _validate_transition(transfer.status, TransferStatus.ONCHAIN_TRANSFER_PENDING)
    net_usd = transfer.source_amount - transfer.quote.platform_fee - transfer.quote.network_fee - transfer.quote.fx_spread
    btx = simulate_usdc_transfer(transfer.id, round(net_usd, 2))
    db.add(btx)
    await _update_status(db, transfer, TransferStatus.ONCHAIN_TRANSFER_PENDING)
    await _emit_event(db, transfer.id, "blockchain.tx_submitted", {"tx_hash": btx.tx_hash, "chain": btx.chain})


async def confirm_onchain_transfer(db: AsyncSession, transfer: Transfer):
    """Simulate blockchain confirmation."""
    _validate_transition(transfer.status, TransferStatus.ONCHAIN_TRANSFER_CONFIRMED)
    for btx in transfer.blockchain_txs:
        if btx.status == "pending":
            simulate_confirmation(btx)
    await _update_status(db, transfer, TransferStatus.ONCHAIN_TRANSFER_CONFIRMED)
    await _emit_event(db, transfer.id, "blockchain.tx_confirmed", {"confirmations": 12})


async def initiate_offramp(db: AsyncSession, transfer: Transfer):
    """Simulate USDC→INR off-ramp."""
    _validate_transition(transfer.status, TransferStatus.USDC_TO_INR_PENDING)
    inr = transfer.target_amount_estimated
    await post_payout_liability(db, transfer, inr)
    await _update_status(db, transfer, TransferStatus.USDC_TO_INR_PENDING)
    await _emit_event(db, transfer.id, "settlement.initiated", {"target_inr": inr})


async def settle_transfer(db: AsyncSession, transfer: Transfer):
    """Mark off-ramp as settled."""
    _validate_transition(transfer.status, TransferStatus.SETTLED)
    inr = transfer.target_amount_estimated
    await post_settlement_completion(db, transfer, inr)
    transfer.target_amount_final = inr
    await _update_status(db, transfer, TransferStatus.SETTLED)
    await _emit_event(db, transfer.id, "settlement.completed", {"final_inr": inr})


async def complete_transfer(db: AsyncSession, transfer: Transfer):
    """Mark transfer as completed and generate benchmark."""
    _validate_transition(transfer.status, TransferStatus.COMPLETED)
    transfer.completed_at = datetime.now(timezone.utc)
    await _update_status(db, transfer, TransferStatus.COMPLETED)
    await _emit_event(db, transfer.id, "transfer.completed")

    # Generate benchmark comparison
    comparison = calculate_comparison(transfer.source_amount, transfer.quote)
    benchmark = Benchmark(
        transfer_id=transfer.id,
        stablecoin_total_fee=comparison["stablecoin_route"]["total_fee_usd"],
        stablecoin_total_time_sec=comparison["stablecoin_route"]["estimated_time_seconds"],
        swift_estimated_fee=comparison["swift_route"]["total_fee_usd"],
        swift_estimated_time_sec=comparison["swift_route"]["estimated_time_seconds"],
    )
    db.add(benchmark)


async def fail_transfer(db: AsyncSession, transfer: Transfer, reason: str = "manual"):
    """Move any non-terminal transfer to failed."""
    if transfer.status in (TransferStatus.COMPLETED.value, TransferStatus.FAILED.value):
        raise InvalidTransition(f"Transfer already in terminal state: {transfer.status}")
    transfer.status = TransferStatus.FAILED.value
    transfer.updated_at = datetime.now(timezone.utc)
    await _emit_event(db, transfer.id, "transfer.failed", {"reason": reason})


# ── Advance helper — runs the next step in the pipeline ─

_ADVANCE_SEQUENCE = [
    (TransferStatus.QUOTED.value, fund_transfer),
    (TransferStatus.FUNDED.value, convert_usd_to_usdc),
    (TransferStatus.USD_TO_USDC_COMPLETE.value, submit_onchain_transfer),
    (TransferStatus.ONCHAIN_TRANSFER_PENDING.value, confirm_onchain_transfer),
    (TransferStatus.ONCHAIN_TRANSFER_CONFIRMED.value, initiate_offramp),
    (TransferStatus.USDC_TO_INR_PENDING.value, settle_transfer),
    (TransferStatus.SETTLED.value, complete_transfer),
]


async def advance_transfer(db: AsyncSession, transfer: Transfer):
    """Advance the transfer by one step in the settlement pipeline."""
    for status_val, handler in _ADVANCE_SEQUENCE:
        if transfer.status == status_val:
            await handler(db, transfer)
            return transfer
    raise InvalidTransition(f"No advance action available for status: {transfer.status}")
