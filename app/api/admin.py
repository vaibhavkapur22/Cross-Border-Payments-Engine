from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import Transfer
from app.services.settlement import advance_transfer, fail_transfer, InvalidTransition

router = APIRouter()


@router.post("/transfers/{transfer_id}/advance")
async def admin_advance(transfer_id: str, db: AsyncSession = Depends(get_db)):
    """Advance a transfer by one step in the settlement pipeline."""
    transfer = await db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(404, "Transfer not found")

    try:
        await advance_transfer(db, transfer)
        await db.commit()
        await db.refresh(transfer)
    except InvalidTransition as e:
        raise HTTPException(400, str(e))

    return {
        "transfer_id": transfer.id,
        "previous_status": None,
        "current_status": transfer.status,
        "message": f"Transfer advanced to {transfer.status}",
    }


@router.post("/transfers/{transfer_id}/fail")
async def admin_fail(transfer_id: str, reason: str = "manual", db: AsyncSession = Depends(get_db)):
    """Force-fail a transfer."""
    transfer = await db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(404, "Transfer not found")

    try:
        await fail_transfer(db, transfer, reason)
        await db.commit()
        await db.refresh(transfer)
    except InvalidTransition as e:
        raise HTTPException(400, str(e))

    return {"transfer_id": transfer.id, "status": transfer.status, "reason": reason}


@router.post("/transfers/{transfer_id}/advance-all")
async def admin_advance_all(transfer_id: str, db: AsyncSession = Depends(get_db)):
    """Run the transfer through the entire settlement pipeline to completion."""
    transfer = await db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(404, "Transfer not found")

    steps = []
    while transfer.status not in ("completed", "failed"):
        prev = transfer.status
        try:
            await advance_transfer(db, transfer)
            steps.append({"from": prev, "to": transfer.status})
        except InvalidTransition:
            break

    await db.commit()
    await db.refresh(transfer)

    return {
        "transfer_id": transfer.id,
        "final_status": transfer.status,
        "steps": steps,
    }
