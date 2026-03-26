import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict

from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("qt_"))
    source_currency: Mapped[str] = mapped_column(String(8), default="USD")
    target_currency: Mapped[str] = mapped_column(String(8), default="INR")
    source_amount: Mapped[float] = mapped_column(Float, nullable=False)
    fx_rate: Mapped[float] = mapped_column(Float, nullable=False)
    fx_source: Mapped[str] = mapped_column(String(32), default="mock")
    platform_fee: Mapped[float] = mapped_column(Float, nullable=False)
    network_fee: Mapped[float] = mapped_column(Float, nullable=False)
    fx_spread: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_target_amount: Mapped[float] = mapped_column(Float, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("tx_"))
    quote_id: Mapped[str] = mapped_column(String(64), ForeignKey("quotes.id"), nullable=False)
    sender_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    recipient_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    recipient_bank_hint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_currency: Mapped[str] = mapped_column(String(8), default="USD")
    target_currency: Mapped[str] = mapped_column(String(8), default="INR")
    source_amount: Mapped[float] = mapped_column(Float, nullable=False)
    target_amount_estimated: Mapped[float] = mapped_column(Float, nullable=False)
    target_amount_final: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    route_type: Mapped[str] = mapped_column(String(32), default="stablecoin")
    status: Mapped[str] = mapped_column(String(48), default="quoted")
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    quote: Mapped[Quote] = relationship("Quote", lazy="joined")
    events: Mapped[List["SettlementEvent"]] = relationship("SettlementEvent", back_populates="transfer", lazy="selectin", order_by="SettlementEvent.created_at")
    blockchain_txs: Mapped[List["BlockchainTransaction"]] = relationship("BlockchainTransaction", back_populates="transfer", lazy="selectin")
    ledger_entries: Mapped[List["LedgerEntry"]] = relationship("LedgerEntry", back_populates="transfer", lazy="selectin")


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("wl_"))
    owner_type: Mapped[str] = mapped_column(String(32), nullable=False)  # treasury, sender, recipient
    owner_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    chain: Mapped[str] = mapped_column(String(32), default="base_sepolia")
    address: Mapped[str] = mapped_column(String(128), nullable=False)
    custody_provider: Mapped[str] = mapped_column(String(64), default="simulated")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("btx_"))
    transfer_id: Mapped[str] = mapped_column(String(64), ForeignKey("transfers.id"), nullable=False)
    chain: Mapped[str] = mapped_column(String(32), default="base_sepolia")
    asset: Mapped[str] = mapped_column(String(16), default="USDC")
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    from_address: Mapped[str] = mapped_column(String(128), nullable=False)
    to_address: Mapped[str] = mapped_column(String(128), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    confirmations: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    transfer: Mapped[Transfer] = relationship("Transfer", back_populates="blockchain_txs")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("le_"))
    transfer_id: Mapped[str] = mapped_column(String(64), ForeignKey("transfers.id"), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(48), nullable=False)
    account_debit: Mapped[str] = mapped_column(String(128), nullable=False)
    account_credit: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transfer: Mapped[Transfer] = relationship("Transfer", back_populates="ledger_entries")


class SettlementEvent(Base):
    __tablename__ = "settlement_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("ev_"))
    transfer_id: Mapped[str] = mapped_column(String(64), ForeignKey("transfers.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    transfer: Mapped[Transfer] = relationship("Transfer", back_populates="events")


class Benchmark(Base):
    __tablename__ = "benchmarks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("bm_"))
    transfer_id: Mapped[str] = mapped_column(String(64), ForeignKey("transfers.id"), unique=True, nullable=False)
    stablecoin_total_fee: Mapped[float] = mapped_column(Float, nullable=False)
    stablecoin_total_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    swift_estimated_fee: Mapped[float] = mapped_column(Float, nullable=False)
    swift_estimated_time_sec: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
