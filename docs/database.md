---
title: Database Schema
layout: default
nav_order: 10
---

# Database Schema
{: .no_toc }

Complete schema reference for all seven database tables powering the payments engine.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Entity Relationship Diagram

```
  ┌──────────┐       ┌────────────┐       ┌──────────────────────┐
  │  quotes  │──1:1──│ transfers  │──1:N──│ ledger_entries       │
  └──────────┘       └─────┬──────┘       └──────────────────────┘
                           │
                    ┌──────┼──────────────┐
                    │      │              │
               ┌────▼───┐ ┌▼───────────┐ ┌▼──────────────┐
               │wallets │ │blockchain_ │ │settlement_    │
               │        │ │transactions│ │events         │
               └────────┘ └────────────┘ └───────────────┘
                                                │
                           ┌────────────────────┘
                      ┌────▼──────┐
                      │benchmarks │
                      └───────────┘
```

## Tables

### `quotes`

FX quotes with fee breakdown and expiry.

| Column | Type | Constraints | Description |
|:-------|:-----|:------------|:------------|
| `id` | VARCHAR | PK | Unique quote identifier |
| `source_currency` | VARCHAR(3) | NOT NULL | Source currency code (e.g., `USD`) |
| `target_currency` | VARCHAR(3) | NOT NULL | Target currency code (e.g., `INR`) |
| `source_amount` | NUMERIC(18,2) | NOT NULL | Amount to send |
| `fx_rate` | NUMERIC(18,6) | NOT NULL | Mid-market FX rate used |
| `fx_source` | VARCHAR(20) | NOT NULL | Rate source (`mock` or `api`) |
| `platform_fee` | NUMERIC(18,2) | NOT NULL | Platform service fee |
| `network_fee` | NUMERIC(18,2) | NOT NULL | Blockchain network fee |
| `fx_spread` | NUMERIC(18,2) | NOT NULL | FX spread amount |
| `estimated_target_amount` | NUMERIC(18,2) | NOT NULL | Estimated recipient amount |
| `expires_at` | TIMESTAMP | NOT NULL | Quote expiration time |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW | Creation timestamp |

---

### `transfers`

Core transfer records tracking the full lifecycle.

| Column | Type | Constraints | Description |
|:-------|:-----|:------------|:------------|
| `id` | VARCHAR | PK | Unique transfer identifier |
| `quote_id` | VARCHAR | FK → quotes.id, NOT NULL | Associated quote |
| `sender_id` | VARCHAR | NOT NULL | Sender identifier |
| `recipient_name` | VARCHAR | NOT NULL | Recipient full name |
| `recipient_bank_hint` | VARCHAR | NOT NULL | Masked bank account |
| `source_currency` | VARCHAR(3) | NOT NULL | Source currency |
| `target_currency` | VARCHAR(3) | NOT NULL | Target currency |
| `source_amount` | NUMERIC(18,2) | NOT NULL | Send amount |
| `target_amount_estimated` | NUMERIC(18,2) | NOT NULL | Estimated receive amount |
| `target_amount_final` | NUMERIC(18,2) | NULLABLE | Final settled amount |
| `route_type` | VARCHAR(20) | NOT NULL, DEFAULT `stablecoin` | Transfer route |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT `created` | Current settlement state |
| `idempotency_key` | VARCHAR | UNIQUE, NULLABLE | Deduplication key |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW | Creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL | Last update timestamp |
| `completed_at` | TIMESTAMP | NULLABLE | Completion timestamp |

**Indexes**: `idempotency_key` (unique), `status`, `sender_id`

---

### `wallets`

Blockchain wallet records (framework for Phase 2 multi-wallet support).

| Column | Type | Constraints | Description |
|:-------|:-----|:------------|:------------|
| `id` | VARCHAR | PK | Unique wallet identifier |
| `owner_type` | VARCHAR(20) | NOT NULL | Owner type (`platform`, `merchant`) |
| `owner_id` | VARCHAR | NOT NULL | Owner identifier |
| `chain` | VARCHAR(20) | NOT NULL | Blockchain network |
| `address` | VARCHAR | NOT NULL | Wallet address |
| `custody_provider` | VARCHAR(50) | NULLABLE | Custody service (e.g., `fireblocks`) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW | Creation timestamp |

---

### `blockchain_transactions`

On-chain USDC transfer records with confirmation tracking.

| Column | Type | Constraints | Description |
|:-------|:-----|:------------|:------------|
| `id` | VARCHAR | PK | Unique record identifier |
| `transfer_id` | VARCHAR | FK → transfers.id, NOT NULL | Associated transfer |
| `chain` | VARCHAR(20) | NOT NULL | Blockchain network (`base_sepolia`) |
| `asset` | VARCHAR(10) | NOT NULL | Token (`USDC`) |
| `amount` | NUMERIC(18,6) | NOT NULL | Transfer amount |
| `from_address` | VARCHAR | NOT NULL | Sender wallet |
| `to_address` | VARCHAR | NOT NULL | Recipient wallet |
| `tx_hash` | VARCHAR | NOT NULL | Transaction hash |
| `confirmations` | INTEGER | NOT NULL, DEFAULT 0 | Block confirmations |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT `submitted` | `submitted` or `confirmed` |
| `submitted_at` | TIMESTAMP | NOT NULL | Submission timestamp |
| `confirmed_at` | TIMESTAMP | NULLABLE | Confirmation timestamp |

**Indexes**: `transfer_id`, `tx_hash`

---

### `ledger_entries`

Double-entry accounting records for all value movements.

| Column | Type | Constraints | Description |
|:-------|:-----|:------------|:------------|
| `id` | VARCHAR | PK | Unique entry identifier |
| `transfer_id` | VARCHAR | FK → transfers.id, NOT NULL | Associated transfer |
| `entry_type` | VARCHAR(20) | NOT NULL | Entry type (see [Ledger System](ledger)) |
| `account_debit` | VARCHAR(50) | NOT NULL | Debited account name |
| `account_credit` | VARCHAR(50) | NOT NULL | Credited account name |
| `amount` | NUMERIC(18,2) | NOT NULL | Entry amount |
| `currency` | VARCHAR(3) | NOT NULL | Currency code |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW | Entry timestamp |

**Indexes**: `transfer_id`, `entry_type`

---

### `settlement_events`

Audit trail of every settlement state transition.

| Column | Type | Constraints | Description |
|:-------|:-----|:------------|:------------|
| `id` | VARCHAR | PK | Unique event identifier |
| `transfer_id` | VARCHAR | FK → transfers.id, NOT NULL | Associated transfer |
| `event_type` | VARCHAR(50) | NOT NULL | Event type string |
| `payload_json` | JSON | NULLABLE | Contextual event data |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW | Event timestamp |

**Indexes**: `transfer_id`, `event_type`

---

### `benchmarks`

Fee and latency comparison results (stablecoin vs SWIFT).

| Column | Type | Constraints | Description |
|:-------|:-----|:------------|:------------|
| `id` | VARCHAR | PK | Unique benchmark identifier |
| `transfer_id` | VARCHAR | FK → transfers.id, NOT NULL | Associated transfer |
| `stablecoin_total_fee` | NUMERIC(18,2) | NOT NULL | Total stablecoin fees (USD) |
| `stablecoin_total_time_sec` | INTEGER | NOT NULL | Stablecoin settlement time |
| `swift_estimated_fee` | NUMERIC(18,2) | NOT NULL | Estimated SWIFT fees (USD) |
| `swift_estimated_time_sec` | INTEGER | NOT NULL | Estimated SWIFT time |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW | Benchmark timestamp |

**Indexes**: `transfer_id`

## Migrations

Database schema is managed via Alembic migrations:

```bash
# Run all pending migrations
alembic upgrade head

# Generate a new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

Migration files are stored in `migrations/versions/`.
