from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.tables import Quote, Transfer, SettlementEvent
from app.models.schemas import (
    TransferRequest,
    TransferResponse,
    TransferTimeline,
    TimelineEvent,
    LedgerEntryOut,
)

router = APIRouter()


def _transfer_response(t: Transfer) -> TransferResponse:
    return TransferResponse(
        transfer_id=t.id,
        quote_id=t.quote_id,
        source_amount=t.source_amount,
        target_amount_estimated=t.target_amount_estimated,
        target_amount_final=t.target_amount_final,
        status=t.status,
        route_type=t.route_type,
        recipient_name=t.recipient_name,
        created_at=t.created_at,
        updated_at=t.updated_at,
        completed_at=t.completed_at,
    )


@router.post("", response_model=TransferResponse, status_code=201)
async def create_transfer(req: TransferRequest, db: AsyncSession = Depends(get_db)):
    # Idempotency check
    if req.idempotency_key:
        existing = (
            await db.execute(
                select(Transfer).where(Transfer.idempotency_key == req.idempotency_key)
            )
        ).scalar_one_or_none()
        if existing:
            return _transfer_response(existing)

    # Validate quote
    quote = await db.get(Quote, req.quote_id)
    if not quote:
        raise HTTPException(404, "Quote not found")
    expires = quote.expires_at if quote.expires_at.tzinfo else quote.expires_at.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(400, "Quote has expired")

    transfer = Transfer(
        quote_id=quote.id,
        recipient_name=req.recipient.name,
        recipient_bank_hint=req.recipient.bank_account_hint,
        source_currency=quote.source_currency,
        target_currency=quote.target_currency,
        source_amount=quote.source_amount,
        target_amount_estimated=quote.estimated_target_amount,
        route_type="stablecoin" if req.route_preference != "swift" else "swift",
        status="quoted",
        idempotency_key=req.idempotency_key,
    )
    db.add(transfer)
    await db.flush()  # ensure transfer.id is populated

    # Initial settlement event
    event = SettlementEvent(
        transfer_id=transfer.id,
        event_type="transfer.created",
        payload_json={"quote_id": quote.id, "recipient": req.recipient.name},
    )
    db.add(event)

    await db.commit()
    await db.refresh(transfer)

    return _transfer_response(transfer)


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(transfer_id: str, db: AsyncSession = Depends(get_db)):
    transfer = await db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(404, "Transfer not found")
    return _transfer_response(transfer)


@router.get("/{transfer_id}/timeline", response_model=TransferTimeline)
async def get_timeline(transfer_id: str, db: AsyncSession = Depends(get_db)):
    transfer = await db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(404, "Transfer not found")

    events = [
        TimelineEvent(
            event_type=e.event_type,
            payload=e.payload_json,
            created_at=e.created_at,
        )
        for e in transfer.events
    ]

    return TransferTimeline(
        transfer_id=transfer.id,
        status=transfer.status,
        events=events,
    )


@router.get("/{transfer_id}/ledger", response_model=list[LedgerEntryOut])
async def get_ledger(transfer_id: str, db: AsyncSession = Depends(get_db)):
    transfer = await db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(404, "Transfer not found")

    return [
        LedgerEntryOut(
            id=e.id,
            entry_type=e.entry_type,
            account_debit=e.account_debit,
            account_credit=e.account_credit,
            amount=e.amount,
            currency=e.currency,
            created_at=e.created_at,
        )
        for e in transfer.ledger_entries
    ]
