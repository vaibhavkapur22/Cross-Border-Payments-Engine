---
title: Architecture
layout: default
nav_order: 3
---

# Architecture
{: .no_toc }

System design, payment lifecycle, and architectural patterns behind the Cross-Border Payments Engine.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## System Overview

The engine follows a layered architecture with clear separation of concerns. Each layer has a single responsibility and communicates through well-defined interfaces.

```
┌──────────────────────────────────────────────────────────┐
│                      API Layer                            │
│   quotes.py │ transfers.py │ admin.py │ comparison.py     │
├──────────────────────────────────────────────────────────┤
│                    Service Layer                          │
│        settlement.py │ fx/engine.py │ comparison/engine   │
├──────────────────────────────────────────────────────────┤
│                 Integration Layer                         │
│          ledger/service.py │ blockchain/simulator.py      │
├──────────────────────────────────────────────────────────┤
│                    Data Layer                             │
│       SQLAlchemy ORM │ Alembic Migrations │ PostgreSQL    │
└──────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Purpose | Key Files |
|:------|:--------|:----------|
| **API** | HTTP endpoints, request validation, response serialization | `app/api/*.py` |
| **Service** | Business logic orchestration, state machine enforcement | `app/services/settlement.py`, `app/fx/engine.py` |
| **Integration** | External system communication (ledger, blockchain) | `app/ledger/service.py`, `app/blockchain/simulator.py` |
| **Data** | ORM models, migrations, database session management | `app/models/tables.py`, `app/database.py` |

## Payment Lifecycle

Every transfer flows through a 10-state settlement state machine. Each transition triggers ledger entries, blockchain operations, and settlement events.

```
                    ┌─────────┐
                    │ created │
                    └────┬────┘
                         │ Quote accepted
                    ┌────▼────┐
                    │ quoted  │
                    └────┬────┘
                         │ Payment funded
                    ┌────▼────┐
                    │ funded  │
                    └────┬────┘
                         │ Treasury converts USD → USDC
              ┌──────────▼───────────┐
              │ usd_to_usdc_complete │
              └──────────┬───────────┘
                         │ Submit to blockchain
           ┌─────────────▼──────────────┐
           │ onchain_transfer_pending   │
           └─────────────┬──────────────┘
                         │ 12 confirmations received
           ┌─────────────▼──────────────┐
           │ onchain_transfer_confirmed │
           └─────────────┬──────────────┘
                         │ Off-ramp initiated
             ┌───────────▼────────────┐
             │ usdc_to_inr_pending    │
             └───────────┬────────────┘
                         │ Off-ramp complete
                    ┌────▼────┐
                    │ settled │
                    └────┬────┘
                         │ Final reconciliation
                   ┌─────▼──────┐
                   │ completed  │
                   └────────────┘

          Any state ──────────▶ failed
```

## Detailed Payment Flow

### Step 1: Quote Creation

The client requests an FX quote via `POST /quotes`. The FX engine:

1. Fetches the mid-market USD/INR rate (83.20 default)
2. Calculates platform fee ($1.50), network fee ($0.35), and FX spread (0.4%)
3. Computes estimated recipient INR amount
4. Sets a 5-minute TTL on the quote

### Step 2: Transfer Initiation

The client creates a transfer via `POST /transfers` with a valid quote ID. The system:

1. Validates the quote hasn't expired
2. Checks idempotency key for duplicate requests
3. Creates the transfer record in `created` status
4. Emits a `transfer.created` settlement event

### Step 3: Funding

The `advance` step simulates receiving the sender's USD payment:

1. Transitions from `created` → `quoted` → `funded`
2. Posts ledger entry: **Debit** `Cash_USD_Omnibus` / **Credit** `Customer_Funding_Liability`
3. Posts fee entry: **Debit** `Customer_Funding_Liability` / **Credit** `Platform_Fee_Revenue`
4. Emits `transfer.funded` event

### Step 4: Treasury Conversion (USD → USDC)

1. Simulates treasury converting USD to USDC
2. Posts ledger entry: **Debit** `USDC_Treasury_Asset` / **Credit** `Customer_Funding_Liability`
3. Transitions to `usd_to_usdc_complete`
4. Emits `treasury.usd_to_usdc.completed` event

### Step 5: Blockchain Transfer

1. Calls the blockchain simulator to create a USDC transaction
2. Generates a simulated transaction hash and wallet addresses
3. Records the `blockchain_transaction` with `submitted` status
4. Transitions to `onchain_transfer_pending`
5. Emits `blockchain.tx_submitted` event

### Step 6: On-Chain Confirmation

1. Simulates 12 block confirmations
2. Updates blockchain transaction status to `confirmed`
3. Transitions to `onchain_transfer_confirmed`
4. Emits `blockchain.tx_confirmed` event

### Step 7: Off-Ramp (USDC → INR)

1. Initiates off-ramp conversion from USDC to INR
2. Posts ledger entry: **Debit** `Recipient_Payout_Liability` / **Credit** `India_Settlement_Clearing`
3. Transitions to `usdc_to_inr_pending`
4. Emits `settlement.initiated` event

### Step 8: Settlement & Completion

1. Simulates local INR payout to recipient bank
2. Posts ledger entry: **Debit** `India_Settlement_Clearing` / **Credit** `Recipient_Settled`
3. Transitions through `settled` → `completed`
4. Records the fee/latency comparison benchmark
5. Emits `settlement.completed` event

## Architectural Patterns

### State Machine Enforcement

Valid transitions are defined as a dictionary in `app/models/enums.py`. Any attempt to transition to an invalid state raises an error:

```python
VALID_TRANSITIONS = {
    "created":                    ["quoted", "failed"],
    "quoted":                     ["funded", "failed"],
    "funded":                     ["usd_to_usdc_complete", "failed"],
    "usd_to_usdc_complete":       ["onchain_transfer_pending", "failed"],
    "onchain_transfer_pending":   ["onchain_transfer_confirmed", "failed"],
    "onchain_transfer_confirmed": ["usdc_to_inr_pending", "failed"],
    "usdc_to_inr_pending":        ["settled", "failed"],
    "settled":                    ["completed", "failed"],
}
```

### Double-Entry Bookkeeping

Every value movement creates a balanced debit/credit pair in the ledger. This ensures:

- **Auditability** — Every dollar is traceable from ingress to egress
- **Reconciliation** — Sum of debits always equals sum of credits
- **Transparency** — Fees, treasury movements, and payouts are all explicit

### Event Sourcing

Each state transition emits a `SettlementEvent` with:
- Event type (e.g., `transfer.funded`, `blockchain.tx_confirmed`)
- JSON payload with contextual data
- Timestamp

The timeline endpoint (`GET /transfers/{id}/timeline`) reconstructs the full history from these events.

### Idempotency

Transfer creation accepts an `idempotency_key`. If a duplicate request arrives with the same key, the original transfer is returned instead of creating a new one. This prevents double-charges from network retries.

### Async-First Design

The entire stack uses async/await:
- **FastAPI** for async request handling
- **SQLAlchemy AsyncSession** for non-blocking database queries
- **AsyncPG** driver for PostgreSQL
- **Celery** for background task execution

This allows the engine to handle many concurrent transfers without blocking on I/O.

## Infrastructure

```
┌─────────┐     ┌─────────┐     ┌────────────┐
│  Client  │────▶│  FastAPI │────▶│ PostgreSQL │
└─────────┘     │  :8000   │     │   :5432    │
                └────┬─────┘     └────────────┘
                     │
                ┌────▼─────┐     ┌────────────┐
                │  Celery   │────▶│   Redis    │
                │  Worker   │     │   :6379    │
                └──────────┘     └────────────┘
```

| Component | Role |
|:----------|:-----|
| **FastAPI** | HTTP API server with async request processing |
| **PostgreSQL** | Primary data store for transfers, ledger, events |
| **Redis** | Celery message broker and result backend |
| **Celery Worker** | Background task execution (future: auto-advancement) |
| **Alembic** | Schema version control and migrations |
