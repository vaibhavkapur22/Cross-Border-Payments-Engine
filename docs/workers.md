---
title: Workers
layout: default
nav_order: 11
---

# Workers
{: .no_toc }

Background task processing with Celery for asynchronous settlement operations.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Overview

The worker layer (`app/workers/celery_app.py`) uses Celery with Redis as the message broker to handle background tasks. In the current MVP, workers provide the framework for automatic settlement progression — in production, transfers would advance through the state machine without manual admin API calls.

## Architecture

```
  FastAPI API                    Celery Worker
  ┌──────────┐     Redis       ┌──────────────┐
  │ Transfer  │───────────────▶│  Process      │
  │ Created   │   Task Queue   │  Settlement   │
  └──────────┘                 │  Steps        │
                               └──────┬───────┘
                                      │
                               ┌──────▼───────┐
                               │  PostgreSQL   │
                               │  (Update DB)  │
                               └──────────────┘
```

## Worker Configuration

| Parameter | Value | Description |
|:----------|:------|:------------|
| Broker | Redis (`redis://localhost:6379/0`) | Message queue backend |
| Result Backend | Redis | Task result storage |
| Concurrency | Default (CPU count) | Worker processes |
| Task Serializer | JSON | Message format |

## Defined Tasks

### Settlement Advancement

The primary task processes a single settlement step for a transfer:

1. Receives a `transfer_id` from the task queue
2. Loads the current transfer state from the database
3. Executes the appropriate handler for the next valid transition
4. Updates the transfer status and emits settlement events
5. Optionally enqueues the next step (chain execution)

### Task Flow

```
  API creates transfer
        │
        ▼
  Enqueue: advance_transfer(transfer_id)
        │
        ▼
  Worker picks up task
        │
        ▼
  Execute settlement step
        │
        ├──▶ Success: Enqueue next step
        │
        └──▶ Failure: Mark transfer failed
```

## Running Workers

### With Docker Compose

Workers start automatically as part of the Docker Compose setup:

```bash
docker compose up -d
```

The `worker` service is configured in `docker-compose.yml`.

### Standalone

```bash
# Start a Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Start with specific concurrency
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
```

### Monitoring

```bash
# Check active workers
celery -A app.workers.celery_app inspect active

# View task queue stats
celery -A app.workers.celery_app inspect stats
```

## Current vs Future State

| Feature | MVP (Current) | Production (Planned) |
|:--------|:-------------|:---------------------|
| Settlement advancement | Manual via admin API | Automatic via Celery tasks |
| Retry on failure | Not implemented | Exponential backoff with max retries |
| Blockchain polling | Simulated instant | Poll for real confirmations |
| Webhook delivery | Not implemented | Async delivery with retries |
| Scheduled tasks | None | Celery Beat for periodic jobs |

## Planned Workers

### Confirmation Poller

Periodically checks pending blockchain transactions for new confirmations:

- **Queue**: `confirmations`
- **Interval**: Every 15 seconds
- **Logic**: Query `blockchain_transactions` where `status = submitted`, check on-chain confirmation count, advance transfers that reach 12 confirmations

### Webhook Dispatcher

Delivers webhook notifications to registered endpoints:

- **Queue**: `webhooks`
- **Retry**: 3 attempts with exponential backoff
- **Logic**: For each settlement event, POST to registered webhook URLs with signed payloads

### Reconciliation Job

Periodic ledger reconciliation check:

- **Queue**: `reconciliation`
- **Schedule**: Hourly via Celery Beat
- **Logic**: Verify all ledger entries balance (debits = credits) per transfer and globally, alert on discrepancies

## Environment Variables

| Variable | Default | Description |
|:---------|:--------|:------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `CELERY_CONCURRENCY` | CPU count | Number of worker processes |
| `CELERY_LOG_LEVEL` | `info` | Worker log verbosity |
