# Cross-Border Payments Engine

A stablecoin-powered remittance engine that settles USD-to-INR transfers over USDC on Base, with double-entry ledger accounting, a settlement state machine, and real-time SWIFT fee benchmarking.

## Getting Started

```bash
# Start Postgres & Redis
docker compose up -d db redis

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000

# Start the Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info
```

## Quick Example

```bash
# Create a quote
curl -X POST http://localhost:8000/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "sender_currency": "USD",
    "recipient_currency": "INR",
    "send_amount": 500.00,
    "recipient_name": "Raj Patel",
    "recipient_bank_hint": "HDFC ****1234"
  }'

# Create a transfer from the quote
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{ "quote_id": "quo_...", "idempotency_key": "remit-001" }'

# Advance through the full settlement pipeline
curl -X POST http://localhost:8000/admin/transfers/{transfer_id}/advance-all

# Compare stablecoin vs SWIFT fees
curl http://localhost:8000/transfers/{transfer_id}/comparison
```
