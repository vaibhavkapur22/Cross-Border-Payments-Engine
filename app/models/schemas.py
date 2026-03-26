from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── Quotes ──────────────────────────────────────────────

class QuoteRequest(BaseModel):
    source_currency: str = "USD"
    target_currency: str = "INR"
    amount: float = Field(gt=0, description="Amount in source currency")
    source_country: str = "US"
    target_country: str = "IN"


class QuoteResponse(BaseModel):
    quote_id: str
    source_amount_usd: float
    fx_rate_usd_inr: float
    platform_fee_usd: float
    network_fee_usd: float
    fx_spread_usd: float
    recipient_amount_inr: float
    expires_at: datetime


# ── Transfers ───────────────────────────────────────────

class RecipientInfo(BaseModel):
    name: str
    bank_account_hint: str = ""


class TransferRequest(BaseModel):
    quote_id: str
    recipient: RecipientInfo
    route_preference: str = "lowest_cost"
    idempotency_key: Optional[str] = None


class TransferResponse(BaseModel):
    transfer_id: str
    quote_id: str
    source_amount: float
    target_amount_estimated: float
    target_amount_final: Optional[float] = None
    status: str
    route_type: str
    recipient_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


# ── Timeline ────────────────────────────────────────────

class TimelineEvent(BaseModel):
    event_type: str
    payload: Optional[Dict] = None
    created_at: datetime


class TransferTimeline(BaseModel):
    transfer_id: str
    status: str
    events: List[TimelineEvent]


# ── Comparison ──────────────────────────────────────────

class RouteBreakdown(BaseModel):
    total_fee_usd: float
    estimated_time_seconds: float
    fee_components: Dict[str, float]


class ComparisonResponse(BaseModel):
    transfer_id: str
    source_amount_usd: float
    stablecoin_route: RouteBreakdown
    swift_route: RouteBreakdown
    fee_savings_usd: float
    time_savings_seconds: float


# ── Ledger ──────────────────────────────────────────────

class LedgerEntryOut(BaseModel):
    id: str
    entry_type: str
    account_debit: str
    account_credit: str
    amount: float
    currency: str
    created_at: datetime
