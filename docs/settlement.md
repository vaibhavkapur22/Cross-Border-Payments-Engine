---
title: Settlement State Machine
layout: default
nav_order: 5
---

# Settlement State Machine
{: .no_toc }

The 10-state lifecycle that governs every cross-border transfer from creation to completion.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Overview

Every transfer in the engine progresses through a deterministic state machine. The settlement service (`app/services/settlement.py`) orchestrates transitions, and each step triggers specific ledger entries, blockchain operations, and audit events.

The state machine enforces **valid transitions only** — any attempt to skip states or make invalid transitions is rejected.

## State Diagram

```
  created ──▶ quoted ──▶ funded ──▶ usd_to_usdc_complete
                                          │
                                          ▼
                              onchain_transfer_pending
                                          │
                                          ▼
                              onchain_transfer_confirmed
                                          │
                                          ▼
                                usdc_to_inr_pending
                                          │
                                          ▼
                                       settled
                                          │
                                          ▼
                                      completed

              ┌──────────────────────────────────┐
              │  Any state can transition to:     │
              │          ▼ failed                  │
              └──────────────────────────────────┘
```

## Valid Transitions

| Current State | Valid Next States |
|:--------------|:------------------|
| `created` | `quoted`, `failed` |
| `quoted` | `funded`, `failed` |
| `funded` | `usd_to_usdc_complete`, `failed` |
| `usd_to_usdc_complete` | `onchain_transfer_pending`, `failed` |
| `onchain_transfer_pending` | `onchain_transfer_confirmed`, `failed` |
| `onchain_transfer_confirmed` | `usdc_to_inr_pending`, `failed` |
| `usdc_to_inr_pending` | `settled`, `failed` |
| `settled` | `completed`, `failed` |
| `completed` | — (terminal) |
| `failed` | — (terminal) |

## State Handlers

Each transition executes a dedicated handler function in the settlement service. These handlers encapsulate the business logic for each step.

### `created → quoted`

**Handler**: Quote acceptance

- Validates the quote hasn't expired (5-minute TTL)
- Links quote data to the transfer
- Emits `transfer.created` event

### `quoted → funded`

**Handler**: Funding receipt

- Simulates receiving the sender's USD payment
- Posts **funding ledger entry**:
  - Debit: `Cash_USD_Omnibus`
  - Credit: `Customer_Funding_Liability`
  - Amount: Source amount in USD
- Posts **fee ledger entry**:
  - Debit: `Customer_Funding_Liability`
  - Credit: `Platform_Fee_Revenue`
  - Amount: Platform fee in USD
- Emits `transfer.funded` event

### `funded → usd_to_usdc_complete`

**Handler**: Treasury conversion

- Simulates treasury converting USD to USDC at market rate
- Posts **treasury ledger entry**:
  - Debit: `USDC_Treasury_Asset`
  - Credit: `Customer_Funding_Liability`
  - Amount: Net amount (source - fees) in USD
- Emits `treasury.usd_to_usdc.completed` event

### `usd_to_usdc_complete → onchain_transfer_pending`

**Handler**: Blockchain submission

- Calls the blockchain simulator to create a USDC transaction
- Generates:
  - Transaction hash (simulated)
  - Sender wallet address
  - Recipient wallet address
- Creates `blockchain_transaction` record with `submitted` status
- Emits `blockchain.tx_submitted` event with `tx_hash` in payload

### `onchain_transfer_pending → onchain_transfer_confirmed`

**Handler**: Confirmation tracking

- Simulates the transaction receiving 12 block confirmations
- Updates `blockchain_transaction`:
  - Sets `confirmations = 12`
  - Sets `status = confirmed`
  - Records `confirmed_at` timestamp
- Emits `blockchain.tx_confirmed` event

### `onchain_transfer_confirmed → usdc_to_inr_pending`

**Handler**: Off-ramp initiation

- Initiates conversion from USDC to INR via off-ramp partner
- Posts **payout ledger entry**:
  - Debit: `Recipient_Payout_Liability`
  - Credit: `India_Settlement_Clearing`
  - Amount: Estimated INR amount
- Emits `settlement.initiated` event

### `usdc_to_inr_pending → settled`

**Handler**: Local payout

- Simulates INR delivery to recipient's bank account
- Posts **settlement ledger entry**:
  - Debit: `India_Settlement_Clearing`
  - Credit: `Recipient_Settled`
  - Amount: Final INR amount
- Emits `settlement.completed` event

### `settled → completed`

**Handler**: Final reconciliation

- Marks the transfer as fully complete
- Sets `completed_at` timestamp
- Sets `target_amount_final` to the settled INR amount
- Records fee/latency comparison benchmark

## Advance Mechanisms

### Single Step

```bash
POST /admin/transfers/{id}/advance
```

Advances the transfer by exactly one state. Useful for debugging or observing intermediate states.

### Full Pipeline

```bash
POST /admin/transfers/{id}/advance-all
```

Executes all remaining steps sequentially until the transfer reaches `completed`. Each step is executed atomically — if any step fails, the transfer stops at that state.

### Force Failure

```bash
POST /admin/transfers/{id}/fail
```

Moves the transfer to `failed` from any non-terminal state. Emits a `transfer.failed` event.

## Error Handling

If a handler encounters an error during a transition:

1. The transfer remains in its current state (no partial transition)
2. A `transfer.failed` event may be emitted depending on the error type
3. The error details are returned in the API response

The state machine guarantees that a transfer is never left in an inconsistent state between two valid states.

## Event Emission

Every state transition emits a `SettlementEvent` that is persisted to the `settlement_events` table:

| Field | Description |
|:------|:------------|
| `id` | Unique event identifier |
| `transfer_id` | Associated transfer |
| `event_type` | Event type string (e.g., `transfer.funded`) |
| `payload_json` | Contextual data as JSON |
| `created_at` | Timestamp of emission |

These events power the timeline endpoint and provide a complete audit trail of every operation performed during settlement.
