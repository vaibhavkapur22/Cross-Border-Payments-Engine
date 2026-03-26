---
title: Comparison Engine
layout: default
nav_order: 9
---

# Comparison Engine
{: .no_toc }

Side-by-side benchmarking of stablecoin transfers against SWIFT for fees, latency, and recipient value.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Overview

The comparison engine (`app/comparison/engine.py`) generates real-time benchmarks that quantify the advantages of stablecoin-powered remittances versus traditional SWIFT transfers. For every completed transfer, it calculates detailed fee and latency breakdowns for both routes and computes the savings.

## Stablecoin Route Breakdown

### Fee Structure

| Component | Amount | Description |
|:----------|:-------|:------------|
| Platform Fee | $1.50 | Service fee |
| Network Fee | $0.35 | Blockchain gas costs |
| FX Spread | $2.00 | 0.4% of $500 |
| Payout Partner Fee | $0.75 | Off-ramp partner cost |
| **Total** | **$4.55** | |

### Latency Breakdown

| Step | Duration | Description |
|:-----|:---------|:------------|
| Funding | 120s (2 min) | Receive sender's USD payment |
| USD → USDC | 30s | Treasury conversion |
| On-chain Transfer | 90s (1.5 min) | USDC transaction broadcast |
| Confirmation | 30s | 12 block confirmations |
| Off-ramp Prep | 180s (3 min) | USDC → INR conversion |
| Local Payout | 300s (5 min) | INR delivery to bank |
| **Total** | **750s (12.5 min)** | |

## SWIFT Route Breakdown

### Fee Structure (Estimated)

| Component | Amount | Description |
|:----------|:-------|:------------|
| Sender Bank Fee | $15.00 | Originating bank wire fee |
| Intermediary Fee | $8.00 | Correspondent bank fee |
| Receiver Fee | $5.00 | Beneficiary bank fee |
| FX Spread | $9.00 | 1.8% retail markup on $500 |
| **Total** | **$37.00** | |

### Latency (Estimated)

| Route | Time |
|:------|:-----|
| SWIFT (total) | ~4 hours (14,400 seconds) |

SWIFT transfers typically settle in 1–5 business days. The 4-hour estimate represents an optimistic same-day scenario.

## Savings Calculation

For a USD 500 → INR transfer:

```
Fee Savings
  SWIFT fees:       $37.00
  Stablecoin fees:   $4.55
  ────────────────────────
  Saved:            $32.45  (87.7%)

Time Savings
  SWIFT time:       14,400s  (4 hours)
  Stablecoin time:     750s  (12.5 minutes)
  ────────────────────────
  Saved:            13,650s  (94.8%)

Recipient Value
  Via SWIFT:        ₹38,432.16  ($463.00 × 83.02*)
  Via Stablecoin:   ₹41,279.88  ($496.15 × 83.20)
  ────────────────────────
  Extra received:    ₹2,847.72

* SWIFT rate includes 1.8% spread baked into the exchange rate
```

## Comparison Response Schema

```json
{
  "transfer_id": "string",
  "stablecoin": {
    "total_fee_usd": 4.55,
    "fee_breakdown": {
      "platform_fee": 1.50,
      "network_fee": 0.35,
      "fx_spread": 2.00,
      "payout_partner_fee": 0.75
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
    "total_fee_usd": 37.00,
    "fee_breakdown": {
      "sender_bank_fee": 15.00,
      "intermediary_fee": 8.00,
      "receiver_fee": 5.00,
      "fx_spread": 9.00
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

## Benchmark Storage

Comparison results are persisted in the `benchmarks` table for analytics:

| Field | Type | Description |
|:------|:-----|:------------|
| `id` | string | Benchmark record identifier |
| `transfer_id` | string | Associated transfer |
| `stablecoin_total_fee` | decimal | Total stablecoin route fees (USD) |
| `stablecoin_total_time_sec` | integer | Total stablecoin settlement time |
| `swift_estimated_fee` | decimal | Estimated SWIFT fees (USD) |
| `swift_estimated_time_sec` | integer | Estimated SWIFT settlement time |
| `created_at` | datetime | When benchmark was recorded |

## Configuration

SWIFT comparison estimates are configurable:

| Variable | Default | Description |
|:---------|:--------|:------------|
| `SWIFT_SENDER_BANK_FEE` | `15.00` | Originating bank fee |
| `SWIFT_INTERMEDIARY_FEE` | `8.00` | Correspondent bank fee |
| `SWIFT_RECEIVER_FEE` | `5.00` | Beneficiary bank fee |
| `SWIFT_FX_SPREAD_PCT` | `0.018` | SWIFT retail FX spread (1.8%) |
