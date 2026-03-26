from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import LedgerEntry, Transfer
from app.models.enums import LedgerEntryType


async def post_funding(db: AsyncSession, transfer: Transfer) -> LedgerEntry:
    """DR Cash_USD_Omnibus / CR Customer_Funding_Liability"""
    entry = LedgerEntry(
        transfer_id=transfer.id,
        entry_type=LedgerEntryType.FUNDING,
        account_debit="Cash_USD_Omnibus",
        account_credit="Customer_Funding_Liability",
        amount=transfer.source_amount,
        currency="USD",
    )
    db.add(entry)
    return entry


async def post_fee_capture(db: AsyncSession, transfer: Transfer) -> LedgerEntry:
    """DR Customer_Funding_Liability / CR Platform_Fee_Revenue"""
    fee = transfer.quote.platform_fee
    entry = LedgerEntry(
        transfer_id=transfer.id,
        entry_type=LedgerEntryType.FEE_CAPTURE,
        account_debit="Customer_Funding_Liability",
        account_credit="Platform_Fee_Revenue",
        amount=fee,
        currency="USD",
    )
    db.add(entry)
    return entry


async def post_treasury_allocation(db: AsyncSession, transfer: Transfer) -> LedgerEntry:
    """DR USDC_Treasury_Asset / CR Customer_Funding_Liability"""
    net = transfer.source_amount - transfer.quote.platform_fee - transfer.quote.network_fee
    entry = LedgerEntry(
        transfer_id=transfer.id,
        entry_type=LedgerEntryType.TREASURY_ALLOCATION,
        account_debit="USDC_Treasury_Asset",
        account_credit="Customer_Funding_Liability",
        amount=round(net, 2),
        currency="USD",
    )
    db.add(entry)
    return entry


async def post_payout_liability(db: AsyncSession, transfer: Transfer, inr_amount: float) -> LedgerEntry:
    """DR Recipient_Payout_Liability / CR India_Settlement_Clearing"""
    entry = LedgerEntry(
        transfer_id=transfer.id,
        entry_type=LedgerEntryType.PAYOUT_LIABILITY,
        account_debit="Recipient_Payout_Liability",
        account_credit="India_Settlement_Clearing",
        amount=inr_amount,
        currency="INR",
    )
    db.add(entry)
    return entry


async def post_settlement_completion(db: AsyncSession, transfer: Transfer, inr_amount: float) -> LedgerEntry:
    """DR India_Settlement_Clearing / CR Recipient_Settled"""
    entry = LedgerEntry(
        transfer_id=transfer.id,
        entry_type=LedgerEntryType.SETTLEMENT_COMPLETION,
        account_debit="India_Settlement_Clearing",
        account_credit="Recipient_Settled",
        amount=inr_amount,
        currency="INR",
    )
    db.add(entry)
    return entry
