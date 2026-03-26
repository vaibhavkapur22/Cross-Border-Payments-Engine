from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.tables import Transfer
from app.models.schemas import ComparisonResponse, RouteBreakdown
from app.comparison.engine import calculate_comparison

router = APIRouter()


@router.get("/transfers/{transfer_id}/comparison", response_model=ComparisonResponse)
async def get_comparison(transfer_id: str, db: AsyncSession = Depends(get_db)):
    transfer = await db.get(Transfer, transfer_id)
    if not transfer:
        raise HTTPException(404, "Transfer not found")

    result = calculate_comparison(transfer.source_amount, transfer.quote)

    return ComparisonResponse(
        transfer_id=transfer.id,
        source_amount_usd=result["source_amount_usd"],
        stablecoin_route=RouteBreakdown(**result["stablecoin_route"]),
        swift_route=RouteBreakdown(**result["swift_route"]),
        fee_savings_usd=result["fee_savings_usd"],
        time_savings_seconds=result["time_savings_seconds"],
    )
