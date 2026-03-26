---
title: FX & Quote Engine
layout: default
nav_order: 6
---

# FX & Quote Engine
{: .no_toc }

FX rate sourcing, fee calculation, and quote generation for cross-border transfers.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Overview

The FX engine (`app/fx/engine.py`) is responsible for generating accurate, transparent quotes that show the sender exactly how much the recipient will receive after all fees and spreads are applied. Each quote has a configurable time-to-live (TTL) and includes a complete fee breakdown.

## Quote Generation Flow

```
   Client Request                    FX Engine
  ┌─────────────┐            ┌──────────────────┐
  │ source: USD  │           │ 1. Fetch FX rate  │
  │ target: INR  │──────────▶│ 2. Calculate fees │
  │ amount: 500  │           │ 3. Apply spread   │
  └─────────────┘           │ 4. Compute target │
                             │ 5. Set expiry     │
                             └────────┬─────────┘
                                      │
                              ┌───────▼────────┐
                              │   Quote Object  │
                              │ rate: 83.20     │
                              │ fees: $3.85     │
                              │ receive: ₹41,280│
                              │ TTL: 5 min      │
                              └────────────────┘
```

## Fee Components

Every quote includes a transparent breakdown of all costs:

| Fee Component | Default Value | Calculation | Description |
|:--------------|:-------------|:------------|:------------|
| **Platform Fee** | $1.50 | Fixed | Service fee charged by the platform |
| **Network Fee** | $0.35 | Fixed | Blockchain gas/network costs |
| **FX Spread** | 0.4% | `source_amount × 0.004` | Markup on mid-market rate |
| **Payout Partner Fee** | $0.75 | Fixed | Off-ramp partner cost (applied at settlement) |

### Fee Calculation Example

For a USD 500 transfer:

```
Platform fee:     $1.50  (fixed)
Network fee:      $0.35  (fixed)
FX spread:        $2.00  (500 × 0.004)
─────────────────────────
Total deducted:   $3.85

Net amount:       $496.15  (500.00 - 3.85)
FX rate:          83.20    (USD/INR mid-market)
─────────────────────────
Recipient gets:   ₹41,279.88  (496.15 × 83.20)
```

{: .note }
The payout partner fee ($0.75) is included in the comparison engine calculations but is not deducted from the quote amount in the MVP. It appears in the full fee comparison against SWIFT.

## FX Rate Source

In the current MVP, the FX rate is sourced from configuration:

| Parameter | Default | Source |
|:----------|:--------|:-------|
| `USD_INR_MID_RATE` | 83.20 | Environment variable / config |

The rate represents the mid-market (interbank) rate. The FX spread is applied on top of this rate as a separate, visible fee — unlike banks that embed their spread in an opaque "retail rate."

### Future: Live Rate Integration

The engine is designed to support live FX rate providers. The `fx_source` field on quotes tracks the rate origin:

| Value | Meaning |
|:------|:--------|
| `mock` | Static configured rate (current) |
| `api` | Live API rate (future) |

## Quote Lifecycle

```
  Created ──────────▶ Used (Transfer created)
     │
     │  (after TTL)
     ▼
  Expired ─────────── Cannot create transfer
```

| Property | Value |
|:---------|:------|
| Default TTL | 300 seconds (5 minutes) |
| Configurable via | `QUOTE_TTL_SECONDS` env var |
| Expiry enforcement | Checked at transfer creation |

A quote can only be used once. Once a transfer is created from a quote, the quote is consumed.

## Quote Response Schema

| Field | Type | Description |
|:------|:-----|:------------|
| `id` | string | Unique quote identifier |
| `source_currency` | string | Source currency (e.g., `"USD"`) |
| `target_currency` | string | Target currency (e.g., `"INR"`) |
| `source_amount` | number | Amount the sender is sending |
| `fx_rate` | number | Mid-market FX rate used |
| `fx_source` | string | Rate source (`"mock"` or `"api"`) |
| `platform_fee` | number | Platform service fee (USD) |
| `network_fee` | number | Blockchain network fee (USD) |
| `fx_spread` | number | FX spread amount (USD) |
| `estimated_target_amount` | number | Estimated amount recipient receives |
| `expires_at` | datetime | Quote expiration timestamp |
| `created_at` | datetime | Quote creation timestamp |

## Configuration

All FX and fee parameters are configurable via environment variables:

| Variable | Default | Description |
|:---------|:--------|:------------|
| `USD_INR_MID_RATE` | `83.20` | USD to INR mid-market rate |
| `STABLECOIN_FX_SPREAD_PCT` | `0.004` | FX spread as decimal (0.4%) |
| `PLATFORM_FEE` | `1.50` | Fixed platform fee (USD) |
| `NETWORK_FEE` | `0.35` | Fixed network fee (USD) |
| `PAYOUT_PARTNER_FEE` | `0.75` | Off-ramp partner fee (USD) |
| `QUOTE_TTL_SECONDS` | `300` | Quote validity period |
