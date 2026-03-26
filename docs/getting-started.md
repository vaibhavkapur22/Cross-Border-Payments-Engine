---
title: Getting Started
layout: default
nav_order: 2
---

# Getting Started
{: .no_toc }

Set up the Cross-Border Payments Engine locally and execute your first USD→INR transfer in minutes.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Prerequisites

| Requirement | Version |
|:------------|:--------|
| Python | 3.12+ |
| Docker & Docker Compose | Latest |
| PostgreSQL | 16+ (or use SQLite for quick start) |
| Redis | 7+ (for Celery workers) |
| Git | 2.x+ |

## Clone the Repository

```bash
git clone https://github.com/vaibhavkapur22/Cross-border-Payments-Engine.git
cd Cross-border-Payments-Engine
```

## Quick Start (SQLite)

The fastest way to get running — uses SQLite and skips Docker dependencies.

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

Verify the server is running:

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok"
}
```

## Docker Compose Setup

For a full production-like environment with PostgreSQL and Redis:

```bash
# Start all services
docker compose up -d

# Verify services are running
docker compose ps
```

This starts four services:

| Service | Port | Description |
|:--------|:-----|:------------|
| `db` | 5432 | PostgreSQL 16 database |
| `redis` | 6379 | Redis 7 message broker |
| `api` | 8000 | FastAPI application (hot reload) |
| `worker` | — | Celery background worker |

## Environment Configuration

Create a `.env` file in the project root. The defaults work out of the box for Docker Compose:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://payments:payments@localhost:5432/cross_border

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# FX Configuration (optional — defaults shown)
USD_INR_MID_RATE=83.20
STABLECOIN_FX_SPREAD_PCT=0.004
PLATFORM_FEE=1.50
NETWORK_FEE=0.35
QUOTE_TTL_SECONDS=300
```

## Run Migrations

```bash
# With Docker Compose
docker compose exec api alembic upgrade head

# Without Docker
alembic upgrade head
```

## Make Your First Transfer

### Step 1: Create a Quote

Request an FX quote for a USD 500 → INR transfer:

```bash
curl -s -X POST http://localhost:8000/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "source_currency": "USD",
    "target_currency": "INR",
    "source_amount": 500.00
  }' | python -m json.tool
```

```json
{
  "id": "q_abc123",
  "source_currency": "USD",
  "target_currency": "INR",
  "source_amount": 500.0,
  "fx_rate": 83.2,
  "platform_fee": 1.5,
  "network_fee": 0.35,
  "fx_spread": 2.0,
  "estimated_target_amount": 41279.88,
  "expires_at": "2026-03-26T12:05:00Z",
  "created_at": "2026-03-26T12:00:00Z"
}
```

The quote is valid for 5 minutes. Fee breakdown:
- **Platform fee**: $1.50
- **Network fee**: $0.35
- **FX spread** (0.4%): $2.00
- **Net amount converted**: $496.15 × 83.20 = **₹41,279.88**

### Step 2: Create a Transfer

Use the quote ID to initiate the transfer:

```bash
curl -s -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "quote_id": "q_abc123",
    "sender_id": "user_001",
    "recipient_name": "Raj Patel",
    "recipient_bank_hint": "HDFC****1234",
    "idempotency_key": "txn-001-unique"
  }' | python -m json.tool
```

```json
{
  "id": "t_xyz789",
  "quote_id": "q_abc123",
  "status": "created",
  "source_amount": 500.0,
  "target_amount_estimated": 41279.88,
  "recipient_name": "Raj Patel",
  "created_at": "2026-03-26T12:00:30Z"
}
```

### Step 3: Execute the Full Pipeline

Use the admin endpoint to advance the transfer through all settlement states:

```bash
curl -s -X POST http://localhost:8000/admin/transfers/t_xyz789/advance-all \
  | python -m json.tool
```

```json
{
  "transfer_id": "t_xyz789",
  "final_status": "completed",
  "steps_executed": 8,
  "message": "Transfer completed successfully"
}
```

### Step 4: View the Timeline

Check the complete event history:

```bash
curl -s http://localhost:8000/transfers/t_xyz789/timeline \
  | python -m json.tool
```

### Step 5: Compare Against SWIFT

See the fee and latency savings:

```bash
curl -s http://localhost:8000/transfers/t_xyz789/comparison \
  | python -m json.tool
```

## Run the Demo Script

A complete end-to-end demo is available:

```bash
chmod +x scripts/demo.sh
./scripts/demo.sh
```

This executes a full USD 500 → INR transfer, advancing through every settlement state and displaying the comparison results.

## What's Next

- [Architecture](architecture) — Understand the system design and payment lifecycle
- [API Reference](api-reference) — Full endpoint documentation
- [Settlement State Machine](settlement) — Deep dive into the 10-state lifecycle
- [Ledger System](ledger) — How double-entry accounting works
