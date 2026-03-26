---
title: Home
layout: home
nav_order: 1
---

# Cross-Border Payments Engine
{: .fs-9 }

A stablecoin-powered remittance engine that enables fast, low-cost USD→INR cross-border transfers using USDC on Base Sepolia.
{: .fs-6 .fw-300 }

[Get Started](getting-started){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[API Reference](api-reference){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## Overview

The Cross-Border Payments Engine is a production-grade remittance infrastructure system that demonstrates how stablecoins can replace legacy SWIFT rails for international money transfers. It provides FX quoting, fee calculation, a settlement state machine, double-entry ledger accounting, and real-time benchmarking against SWIFT fees and latency.

Built with **FastAPI**, **SQLAlchemy**, and **Celery**, the engine processes a USD 500 transfer to India in under 13 minutes at ~$4.55 in fees — compared to SWIFT's ~$37 and 4+ hour settlement time.

## Key Features

- **FX Quote Engine** — Real-time USD/INR quotes with transparent fee breakdown (platform, network, FX spread)
- **Settlement State Machine** — 10-state lifecycle with enforced valid transitions and event sourcing
- **Double-Entry Ledger** — Full accounting trail for every value movement across the transfer lifecycle
- **Blockchain Integration** — Simulated USDC transfers on Base Sepolia with transaction tracking
- **SWIFT Benchmarking** — Side-by-side fee and latency comparison against incumbent rails
- **Idempotent Transfers** — Safe retries via idempotency keys on transfer creation
- **Admin Controls** — Manual state advancement and failure injection for testing
- **Event Timeline** — Chronological audit trail of every settlement step

## Architecture at a Glance

```
┌─────────────┐     ┌──────────────────────────────────────────────┐
│   Client     │     │          Cross-Border Payments Engine         │
│  (REST API)  │────▶│                                              │
└─────────────┘     │  ┌──────────┐  ┌────────────┐  ┌──────────┐ │
                    │  │  Quotes  │  │  Transfers  │  │  Admin   │ │
                    │  │   API    │  │    API      │  │   API    │ │
                    │  └────┬─────┘  └─────┬──────┘  └────┬─────┘ │
                    │       │              │               │       │
                    │  ┌────▼──────────────▼───────────────▼─────┐ │
                    │  │           Service Layer                  │ │
                    │  │  ┌──────────┐ ┌─────────┐ ┌──────────┐ │ │
                    │  │  │ FX Engine│ │Settlement│ │Comparison│ │ │
                    │  │  └──────────┘ │ Service  │ │  Engine  │ │ │
                    │  │               └─────────┘ └──────────┘ │ │
                    │  └────────────────────┬──────────────────┘ │
                    │                       │                     │
                    │  ┌────────────────────▼──────────────────┐ │
                    │  │          Data & Integration Layer       │ │
                    │  │  ┌──────┐ ┌──────────┐ ┌───────────┐ │ │
                    │  │  │Ledger│ │Blockchain │ │  Database  │ │ │
                    │  │  │      │ │ Simulator │ │(PostgreSQL)│ │ │
                    │  │  └──────┘ └──────────┘ └───────────┘ │ │
                    │  └──────────────────────────────────────┘ │
                    └──────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|:----------|:-----------|
| **Backend Framework** | FastAPI 0.115 + Uvicorn |
| **Database** | PostgreSQL 16 / SQLite (dev) |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migrations** | Alembic 1.14 |
| **Task Queue** | Celery 5.4 + Redis 7 |
| **Validation** | Pydantic 2.10 |
| **Blockchain** | Base Sepolia (simulated USDC) |
| **Containerization** | Docker + Docker Compose |
| **Language** | Python 3.12 |

## Project Structure

```
Cross-border Payments Engine/
├── app/
│   ├── api/                    # FastAPI route handlers
│   │   ├── admin.py            # Settlement state controls
│   │   ├── comparison.py       # Stablecoin vs SWIFT comparison
│   │   ├── quotes.py           # FX quote generation
│   │   └── transfers.py        # Transfer CRUD & timeline
│   ├── blockchain/
│   │   └── simulator.py        # Simulated USDC transfers
│   ├── comparison/
│   │   └── engine.py           # Fee & latency benchmarking
│   ├── fx/
│   │   └── engine.py           # FX rate & quote calculation
│   ├── ledger/
│   │   └── service.py          # Double-entry ledger posting
│   ├── models/
│   │   ├── enums.py            # State machine & transitions
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── tables.py           # SQLAlchemy ORM tables
│   ├── services/
│   │   └── settlement.py       # Settlement orchestration
│   ├── workers/
│   │   └── celery_app.py       # Background task definitions
│   ├── config.py               # Application settings
│   ├── database.py             # Async DB engine & sessions
│   └── main.py                 # FastAPI app entrypoint
├── migrations/                  # Alembic migration scripts
├── scripts/
│   └── demo.sh                 # End-to-end demo script
├── tests/                       # Test suite
├── docker-compose.yml           # Local dev environment
├── Dockerfile                   # Container image
├── requirements.txt             # Python dependencies
└── alembic.ini                  # Migration configuration
```
