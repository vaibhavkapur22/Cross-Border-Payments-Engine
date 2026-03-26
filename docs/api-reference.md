---
title: API Reference
layout: default
nav_order: 4
---

# API Reference
{: .no_toc }

Complete REST API documentation for the Cross-Border Payments Engine.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Base URL

```
http://localhost:8000
```

All endpoints accept and return JSON. The API is documented via OpenAPI and can be explored interactively at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc).

## Health Check

### `GET /health`

Returns the server status.

```bash
curl http://localhost:8000/health
```

**Response** `200 OK`

```json
{
  "status": "ok"
}
```

---

## Quotes

### `POST /quotes`

Create an FX quote for a cross-border transfer.

**Request Body**

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `source_currency` | string | Yes | Source currency code (e.g., `"USD"`) |
| `target_currency` | string | Yes | Target currency code (e.g., `"INR"`) |
| `source_amount` | number | Yes | Amount to send in source currency |

```bash
curl -X POST http://localhost:8000/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "source_currency": "USD",
    "target_currency": "INR",
    "source_amount": 500.00
  }'
```

**Response** `200 OK`

```json
{
  "id": "q_550e8400-e29b-41d4-a716-446655440000",
  "source_currency": "USD",
  "target_currency": "INR",
  "source_amount": 500.0,
  "fx_rate": 83.2,
  "fx_source": "mock",
  "platform_fee": 1.5,
  "network_fee": 0.35,
  "fx_spread": 2.0,
  "estimated_target_amount": 41279.88,
  "expires_at": "2026-03-26T12:05:00Z",
  "created_at": "2026-03-26T12:00:00Z"
}
```

**Fee Calculation Logic**

```
fx_spread      = source_amount × stablecoin_fx_spread_pct  (0.4%)
total_fees     = platform_fee + network_fee + fx_spread
net_amount     = source_amount - total_fees
target_amount  = net_amount × fx_rate
```

---

### `GET /quotes/{quote_id}`

Retrieve an existing quote by ID.

```bash
curl http://localhost:8000/quotes/q_550e8400-e29b-41d4-a716-446655440000
```

**Response** `200 OK`

Returns the same schema as the create response.

**Error Responses**

| Status | Description |
|:-------|:------------|
| `404` | Quote not found |

---

## Transfers

### `POST /transfers`

Create a transfer from a valid, unexpired quote.

**Request Body**

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `quote_id` | string | Yes | ID of a valid quote |
| `sender_id` | string | Yes | Sender identifier |
| `recipient_name` | string | Yes | Recipient's full name |
| `recipient_bank_hint` | string | Yes | Masked bank account (e.g., `"HDFC****1234"`) |
| `idempotency_key` | string | No | Unique key to prevent duplicate transfers |

```bash
curl -X POST http://localhost:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "quote_id": "q_550e8400-e29b-41d4-a716-446655440000",
    "sender_id": "user_001",
    "recipient_name": "Raj Patel",
    "recipient_bank_hint": "HDFC****1234",
    "idempotency_key": "txn-unique-001"
  }'
```

**Response** `200 OK`

```json
{
  "id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "quote_id": "q_550e8400-e29b-41d4-a716-446655440000",
  "sender_id": "user_001",
  "recipient_name": "Raj Patel",
  "recipient_bank_hint": "HDFC****1234",
  "source_currency": "USD",
  "target_currency": "INR",
  "source_amount": 500.0,
  "target_amount_estimated": 41279.88,
  "target_amount_final": null,
  "route_type": "stablecoin",
  "status": "created",
  "idempotency_key": "txn-unique-001",
  "created_at": "2026-03-26T12:00:30Z",
  "updated_at": "2026-03-26T12:00:30Z",
  "completed_at": null
}
```

**Error Responses**

| Status | Description |
|:-------|:------------|
| `400` | Quote expired or invalid |
| `404` | Quote not found |
| `409` | Idempotency key conflict (different quote_id) |

{: .note }
If a request is made with an `idempotency_key` that already exists, and the `quote_id` matches, the original transfer is returned (no new transfer created). This makes retries safe.

---

### `GET /transfers/{transfer_id}`

Retrieve a transfer by ID.

```bash
curl http://localhost:8000/transfers/t_7c9e6679-7425-40de-944b-e07fc1f90ae7
```

**Response** `200 OK`

Returns the full transfer object with current status.

---

### `GET /transfers/{transfer_id}/timeline`

Get the chronological event timeline for a transfer.

```bash
curl http://localhost:8000/transfers/t_7c9e6679-7425-40de-944b-e07fc1f90ae7/timeline
```

**Response** `200 OK`

```json
[
  {
    "id": "evt_001",
    "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "event_type": "transfer.created",
    "payload_json": {},
    "created_at": "2026-03-26T12:00:30Z"
  },
  {
    "id": "evt_002",
    "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "event_type": "transfer.funded",
    "payload_json": {
      "amount": 500.0,
      "currency": "USD"
    },
    "created_at": "2026-03-26T12:00:31Z"
  },
  {
    "id": "evt_003",
    "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "event_type": "treasury.usd_to_usdc.completed",
    "payload_json": {
      "usdc_amount": 496.15
    },
    "created_at": "2026-03-26T12:01:00Z"
  },
  {
    "id": "evt_004",
    "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "event_type": "blockchain.tx_submitted",
    "payload_json": {
      "tx_hash": "0xabc123...",
      "chain": "base_sepolia"
    },
    "created_at": "2026-03-26T12:01:30Z"
  }
]
```

**Event Types**

| Event | Emitted When |
|:------|:-------------|
| `transfer.created` | Transfer record created |
| `transfer.funded` | Sender payment received |
| `transfer.failed` | Transfer moved to failed state |
| `treasury.usd_to_usdc.completed` | Treasury converts USD to USDC |
| `blockchain.tx_submitted` | USDC transaction submitted on-chain |
| `blockchain.tx_confirmed` | Transaction reaches 12 confirmations |
| `settlement.initiated` | Off-ramp USDC → INR started |
| `settlement.completed` | INR payout delivered to recipient |

---

### `GET /transfers/{transfer_id}/ledger`

Get all ledger entries for a transfer.

```bash
curl http://localhost:8000/transfers/t_7c9e6679-7425-40de-944b-e07fc1f90ae7/ledger
```

**Response** `200 OK`

```json
[
  {
    "id": "le_001",
    "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "entry_type": "funding",
    "account_debit": "Cash_USD_Omnibus",
    "account_credit": "Customer_Funding_Liability",
    "amount": 500.0,
    "currency": "USD",
    "created_at": "2026-03-26T12:00:31Z"
  },
  {
    "id": "le_002",
    "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "entry_type": "fee",
    "account_debit": "Customer_Funding_Liability",
    "account_credit": "Platform_Fee_Revenue",
    "amount": 1.5,
    "currency": "USD",
    "created_at": "2026-03-26T12:00:31Z"
  }
]
```

---

## Comparison

### `GET /transfers/{transfer_id}/comparison`

Get a fee and latency comparison between the stablecoin route and SWIFT for this transfer.

```bash
curl http://localhost:8000/transfers/t_7c9e6679-7425-40de-944b-e07fc1f90ae7/comparison
```

**Response** `200 OK`

```json
{
  "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "stablecoin": {
    "total_fee_usd": 4.55,
    "fee_breakdown": {
      "platform_fee": 1.5,
      "network_fee": 0.35,
      "fx_spread": 2.0,
      "payout_partner_fee": 0.7
    },
    "total_time_seconds": 750,
    "time_breakdown": {
      "funding": 120,
      "usd_to_usdc": 30,
      "onchain_transfer": 90,
      "confirmation": 30,
      "offramp_prep": 180,
      "local_payout": 300
    },
    "recipient_receives_inr": 41279.88
  },
  "swift": {
    "total_fee_usd": 37.0,
    "fee_breakdown": {
      "sender_bank_fee": 15.0,
      "intermediary_fee": 8.0,
      "receiver_fee": 5.0,
      "fx_spread": 9.0
    },
    "total_time_seconds": 14400,
    "recipient_receives_inr": 38432.16
  },
  "savings": {
    "fee_saved_usd": 32.45,
    "fee_saved_pct": 87.7,
    "time_saved_seconds": 13650,
    "time_saved_pct": 94.8,
    "extra_inr_received": 2847.72
  }
}
```

---

## Admin

Admin endpoints for testing and simulation. These allow manual control of the settlement pipeline.

{: .warning }
Admin endpoints are intended for development and testing only. In production, state advancement should be handled by background workers.

### `POST /admin/transfers/{transfer_id}/advance`

Advance a transfer by one settlement state.

```bash
curl -X POST http://localhost:8000/admin/transfers/t_7c9e6679-7425-40de-944b-e07fc1f90ae7/advance
```

**Response** `200 OK`

```json
{
  "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "previous_status": "created",
  "new_status": "quoted",
  "message": "Transfer advanced successfully"
}
```

---

### `POST /admin/transfers/{transfer_id}/advance-all`

Execute the entire settlement pipeline from current state to `completed`.

```bash
curl -X POST http://localhost:8000/admin/transfers/t_7c9e6679-7425-40de-944b-e07fc1f90ae7/advance-all
```

**Response** `200 OK`

```json
{
  "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "final_status": "completed",
  "steps_executed": 8,
  "message": "Transfer completed successfully"
}
```

---

### `POST /admin/transfers/{transfer_id}/fail`

Force a transfer into the `failed` state from any current state.

```bash
curl -X POST http://localhost:8000/admin/transfers/t_7c9e6679-7425-40de-944b-e07fc1f90ae7/fail
```

**Response** `200 OK`

```json
{
  "transfer_id": "t_7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "previous_status": "funded",
  "new_status": "failed",
  "message": "Transfer failed"
}
```

---

## Transfer Statuses

| Status | Description |
|:-------|:------------|
| `created` | Transfer record created, awaiting funding |
| `quoted` | Quote attached and accepted |
| `funded` | Sender payment received |
| `usd_to_usdc_complete` | Treasury converted USD to USDC |
| `onchain_transfer_pending` | USDC transaction submitted on-chain |
| `onchain_transfer_confirmed` | Transaction confirmed (12 blocks) |
| `usdc_to_inr_pending` | Off-ramp USDC → INR initiated |
| `settled` | INR delivered to recipient bank |
| `completed` | Transfer fully reconciled |
| `failed` | Transfer failed (terminal state) |

## Error Format

All error responses follow a consistent format:

```json
{
  "detail": "Quote not found"
}
```

| Status Code | Meaning |
|:------------|:--------|
| `400` | Bad request (validation error, expired quote) |
| `404` | Resource not found |
| `409` | Conflict (idempotency key mismatch) |
| `422` | Unprocessable entity (invalid request body) |
| `500` | Internal server error |
