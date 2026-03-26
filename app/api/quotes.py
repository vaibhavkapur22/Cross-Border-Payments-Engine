from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.tables import Quote
from app.models.schemas import QuoteRequest, QuoteResponse
from app.fx.engine import calculate_quote

router = APIRouter()


@router.post("", response_model=QuoteResponse, status_code=201)
async def create_quote(req: QuoteRequest, db: AsyncSession = Depends(get_db)):
    if req.source_currency != "USD" or req.target_currency != "INR":
        raise HTTPException(400, "Only USD→INR corridor is supported in MVP")

    result = calculate_quote(req.amount)

    quote = Quote(
        source_currency=req.source_currency,
        target_currency=req.target_currency,
        source_amount=req.amount,
        fx_rate=result["fx_rate"],
        fx_source=result["fx_source"],
        platform_fee=result["platform_fee"],
        network_fee=result["network_fee"],
        fx_spread=result["fx_spread"],
        estimated_target_amount=result["recipient_amount_inr"],
        expires_at=result["expires_at"],
    )
    db.add(quote)
    await db.commit()
    await db.refresh(quote)

    return QuoteResponse(
        quote_id=quote.id,
        source_amount_usd=quote.source_amount,
        fx_rate_usd_inr=quote.fx_rate,
        platform_fee_usd=quote.platform_fee,
        network_fee_usd=quote.network_fee,
        fx_spread_usd=quote.fx_spread,
        recipient_amount_inr=quote.estimated_target_amount,
        expires_at=quote.expires_at,
    )


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: str, db: AsyncSession = Depends(get_db)):
    quote = await db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(404, "Quote not found")

    return QuoteResponse(
        quote_id=quote.id,
        source_amount_usd=quote.source_amount,
        fx_rate_usd_inr=quote.fx_rate,
        platform_fee_usd=quote.platform_fee,
        network_fee_usd=quote.network_fee,
        fx_spread_usd=quote.fx_spread,
        recipient_amount_inr=quote.estimated_target_amount,
        expires_at=quote.expires_at,
    )
