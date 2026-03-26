---
title: Configuration
layout: default
nav_order: 12
---

# Configuration
{: .no_toc }

Environment variables, settings, and configuration options for the Cross-Border Payments Engine.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Overview

All configuration is managed via environment variables, loaded through Pydantic Settings (`app/config.py`). Defaults are provided for local development — override with a `.env` file or environment variables for production.

## Database

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./cross_border.db` | Async database connection URL |

**PostgreSQL example**:
```
DATABASE_URL=postgresql+asyncpg://payments:payments@localhost:5432/cross_border
```

**SQLite example** (development):
```
DATABASE_URL=sqlite+aiosqlite:///./cross_border.db
```

## Redis

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection for Celery broker |

## FX & Pricing

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `USD_INR_MID_RATE` | No | `83.20` | USD to INR mid-market exchange rate |
| `STABLECOIN_FX_SPREAD_PCT` | No | `0.004` | Stablecoin route FX spread (0.4%) |
| `PLATFORM_FEE` | No | `1.50` | Fixed platform service fee (USD) |
| `NETWORK_FEE` | No | `0.35` | Fixed blockchain network fee (USD) |
| `PAYOUT_PARTNER_FEE` | No | `0.75` | Off-ramp partner fee (USD) |
| `QUOTE_TTL_SECONDS` | No | `300` | Quote validity period in seconds |

## SWIFT Comparison

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `SWIFT_SENDER_BANK_FEE` | No | `15.00` | SWIFT originating bank fee (USD) |
| `SWIFT_INTERMEDIARY_FEE` | No | `8.00` | SWIFT correspondent bank fee (USD) |
| `SWIFT_RECEIVER_FEE` | No | `5.00` | SWIFT beneficiary bank fee (USD) |
| `SWIFT_FX_SPREAD_PCT` | No | `0.018` | SWIFT retail FX spread (1.8%) |

## API Server

| Variable | Required | Default | Description |
|:---------|:---------|:--------|:------------|
| `HOST` | No | `0.0.0.0` | Server bind address |
| `PORT` | No | `8000` | Server port |
| `RELOAD` | No | `true` | Enable hot reload (development) |

## Complete `.env` Example

```bash
# Database
DATABASE_URL=postgresql+asyncpg://payments:payments@localhost:5432/cross_border

# Redis
REDIS_URL=redis://localhost:6379/0

# FX Configuration
USD_INR_MID_RATE=83.20
STABLECOIN_FX_SPREAD_PCT=0.004
PLATFORM_FEE=1.50
NETWORK_FEE=0.35
PAYOUT_PARTNER_FEE=0.75
QUOTE_TTL_SECONDS=300

# SWIFT Comparison
SWIFT_SENDER_BANK_FEE=15.00
SWIFT_INTERMEDIARY_FEE=8.00
SWIFT_RECEIVER_FEE=5.00
SWIFT_FX_SPREAD_PCT=0.018

# Server
HOST=0.0.0.0
PORT=8000
```

{: .warning }
Never commit `.env` files to version control. Add `.env` to your `.gitignore` file. The repository includes sensible defaults for all configuration values — a `.env` file is only needed to override them.

## Docker Compose Services

The `docker-compose.yml` defines four services with pre-configured environment variables:

| Service | Image | Port | Key Config |
|:--------|:------|:-----|:-----------|
| `db` | postgres:16 | 5432 | `POSTGRES_DB=cross_border`, `POSTGRES_USER=payments` |
| `redis` | redis:7-alpine | 6379 | Default configuration |
| `api` | ./Dockerfile | 8000 | `DATABASE_URL`, `REDIS_URL`, hot reload enabled |
| `worker` | ./Dockerfile | — | `REDIS_URL`, Celery worker command |

### Starting Services

```bash
# All services
docker compose up -d

# Only infrastructure (for local development)
docker compose up -d db redis

# View logs
docker compose logs -f api

# Stop all services
docker compose down
```

## Settings Class

Configuration is loaded via Pydantic Settings in `app/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./cross_border.db"

    # FX
    usd_inr_mid_rate: float = 83.20
    stablecoin_fx_spread_pct: float = 0.004

    # Fees
    platform_fee: float = 1.50
    network_fee: float = 0.35
    payout_partner_fee: float = 0.75

    # Quote
    quote_ttl_seconds: int = 300

    # SWIFT estimates
    swift_sender_bank_fee: float = 15.00
    swift_intermediary_fee: float = 8.00
    swift_receiver_fee: float = 5.00
    swift_fx_spread_pct: float = 0.018

    class Config:
        env_file = ".env"
```

Settings are accessed throughout the application via a singleton instance, ensuring consistent configuration across all components.
