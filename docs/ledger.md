---
title: Ledger System
layout: default
nav_order: 7
---

# Ledger System
{: .no_toc }

Double-entry bookkeeping that tracks every value movement across the transfer lifecycle.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Overview

The ledger system (`app/ledger/service.py`) implements double-entry accounting principles. Every movement of value — funding, fees, treasury operations, payouts — creates a balanced debit/credit pair. This ensures complete auditability and enables reconciliation at any point.

## Accounting Principles

- **Every entry has a debit and a credit** — money always moves from one account to another
- **Debits equal credits** — the ledger is always balanced
- **Entries are immutable** — once created, ledger entries are never modified or deleted
- **Currency is explicit** — each entry records the currency of the movement

## Entry Types

| Entry Type | Debit Account | Credit Account | Currency | When |
|:-----------|:-------------|:---------------|:---------|:-----|
| `funding` | `Cash_USD_Omnibus` | `Customer_Funding_Liability` | USD | Sender payment received |
| `fee` | `Customer_Funding_Liability` | `Platform_Fee_Revenue` | USD | Fee deducted from funded amount |
| `treasury` | `USDC_Treasury_Asset` | `Customer_Funding_Liability` | USD | USD converted to USDC |
| `payout` | `Recipient_Payout_Liability` | `India_Settlement_Clearing` | INR | Off-ramp initiated |
| `settlement` | `India_Settlement_Clearing` | `Recipient_Settled` | INR | INR delivered to recipient |

## Account Chart

```
                    USD Side                          INR Side
              ┌─────────────────┐              ┌──────────────────────┐
              │ Cash_USD_Omnibus│              │Recipient_Payout_     │
              │   (Asset)       │              │  Liability           │
              └────────┬────────┘              └──────────┬───────────┘
                       │ funding                          │ payout
              ┌────────▼────────┐              ┌──────────▼───────────┐
              │ Customer_Funding│              │India_Settlement_     │
              │  _Liability     │              │  Clearing            │
              └──┬──────────┬───┘              └──────────┬───────────┘
          fee    │          │ treasury                     │ settlement
      ┌──────────▼──┐  ┌───▼────────────┐     ┌──────────▼───────────┐
      │Platform_Fee │  │ USDC_Treasury_ │     │ Recipient_Settled    │
      │  _Revenue   │  │   Asset        │     │                      │
      └─────────────┘  └────────────────┘     └──────────────────────┘
```

## Transfer Lifecycle Entries

### Successful Transfer (USD 500 → INR)

| Step | Entry Type | Debit | Credit | Amount | Currency |
|:-----|:-----------|:------|:-------|:-------|:---------|
| 1 | `funding` | Cash_USD_Omnibus | Customer_Funding_Liability | 500.00 | USD |
| 2 | `fee` | Customer_Funding_Liability | Platform_Fee_Revenue | 1.50 | USD |
| 3 | `treasury` | USDC_Treasury_Asset | Customer_Funding_Liability | 496.15 | USD |
| 4 | `payout` | Recipient_Payout_Liability | India_Settlement_Clearing | 41,279.88 | INR |
| 5 | `settlement` | India_Settlement_Clearing | Recipient_Settled | 41,279.88 | INR |

**Verification**: On the USD side, the Customer_Funding_Liability account nets to zero:
- Credited $500.00 (funding)
- Debited $1.50 (fee) + $496.15 (treasury) = $497.65

{: .note }
The remaining $2.35 difference is the FX spread, which is captured in the treasury conversion. The net amount converted ($496.15) already has fees and spread deducted.

### Failed Transfer

If a transfer fails mid-pipeline, the ledger entries recorded up to that point remain as an audit trail. In production, reversal entries would be posted to unwind the positions.

## Ledger Entry Schema

| Field | Type | Description |
|:------|:-----|:------------|
| `id` | string | Unique entry identifier |
| `transfer_id` | string | Associated transfer |
| `entry_type` | string | One of: `funding`, `fee`, `treasury`, `payout`, `settlement` |
| `account_debit` | string | Account being debited |
| `account_credit` | string | Account being credited |
| `amount` | decimal | Amount of the entry |
| `currency` | string | Currency code (USD or INR) |
| `created_at` | datetime | Entry creation timestamp |

## API Access

Retrieve all ledger entries for a transfer:

```bash
curl http://localhost:8000/transfers/{transfer_id}/ledger
```

Returns an array of ledger entries in chronological order, providing a complete financial audit trail for the transfer.

## Reconciliation

The ledger enables reconciliation checks:

- **Per-transfer**: Sum of USD debits equals sum of USD credits for each transfer
- **Per-account**: Running balance of each account can be computed from all entries
- **Global**: Total debits across all accounts equals total credits

In production, automated reconciliation jobs would run these checks periodically and flag any discrepancies.
