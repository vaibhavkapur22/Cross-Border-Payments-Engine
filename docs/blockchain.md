---
title: Blockchain Integration
layout: default
nav_order: 8
---

# Blockchain Integration
{: .no_toc }

Simulated USDC transfers on Base Sepolia with transaction tracking and confirmation monitoring.
{: .fs-6 .fw-300 }

1. TOC
{:toc}

---

## Overview

The blockchain layer (`app/blockchain/simulator.py`) handles USDC transfer operations on the Base Sepolia testnet. In the current MVP, all blockchain interactions are **simulated** — no actual on-chain transactions occur. The simulator generates realistic transaction data that exercises the full settlement pipeline.

## Simulation Architecture

```
  Settlement Service
        │
        ▼
  ┌─────────────────────┐
  │ Blockchain Simulator │
  │                     │
  │  submit_transfer()  │──▶ Generates fake tx_hash
  │  confirm_transfer() │──▶ Simulates 12 confirmations
  │  get_tx_status()    │──▶ Returns tx details
  └─────────────────────┘
        │
        ▼
  blockchain_transactions table
```

## Simulated Operations

### Transaction Submission

When a transfer reaches the `usd_to_usdc_complete` state, the simulator:

1. Generates a random transaction hash (64-character hex string)
2. Generates sender and recipient wallet addresses (40-character hex)
3. Creates a `blockchain_transaction` record with status `submitted`
4. Returns the transaction hash for tracking

**Generated Data Example**:

| Field | Value |
|:------|:------|
| `tx_hash` | `0x7a8b9c...def456` |
| `chain` | `base_sepolia` |
| `asset` | `USDC` |
| `from_address` | `0x1234...abcd` |
| `to_address` | `0x5678...ef01` |
| `amount` | 496.15 |
| `status` | `submitted` |
| `confirmations` | 0 |

### Transaction Confirmation

When advancing from `onchain_transfer_pending`, the simulator:

1. Sets confirmations to 12 (the required threshold)
2. Updates status from `submitted` to `confirmed`
3. Records the `confirmed_at` timestamp

### Confirmation Threshold

| Parameter | Value | Description |
|:----------|:------|:------------|
| Required confirmations | 12 | Number of block confirmations needed |
| Confirmation time | ~30 seconds | Simulated time for confirmations |

{: .note }
Base Sepolia has ~2 second block times, so 12 confirmations would take ~24 seconds in reality. The simulator reflects this in the timing estimates.

## Blockchain Transaction Schema

| Field | Type | Description |
|:------|:-----|:------------|
| `id` | string | Unique record identifier |
| `transfer_id` | string | Associated payment transfer |
| `chain` | string | Blockchain network (`base_sepolia`) |
| `asset` | string | Token being transferred (`USDC`) |
| `amount` | decimal | USDC amount transferred |
| `from_address` | string | Sender wallet address |
| `to_address` | string | Recipient wallet address |
| `tx_hash` | string | On-chain transaction hash |
| `confirmations` | integer | Current confirmation count |
| `status` | string | `submitted` or `confirmed` |
| `submitted_at` | datetime | When the tx was broadcast |
| `confirmed_at` | datetime | When 12 confirmations reached |

## Settlement Events

The blockchain layer emits two events during the transfer lifecycle:

| Event | Payload | Emitted When |
|:------|:--------|:-------------|
| `blockchain.tx_submitted` | `tx_hash`, `chain`, `from_address`, `to_address` | Transaction broadcast to network |
| `blockchain.tx_confirmed` | `tx_hash`, `confirmations`, `confirmed_at` | 12 confirmations reached |

## Future: Live Testnet Integration

The simulator is designed to be replaced with real blockchain interactions in Phase 2:

| Phase | Behavior |
|:------|:---------|
| **Phase A (Current)** | Fully simulated — no real blockchain calls |
| **Phase B (Planned)** | Real USDC transfers on Base Sepolia testnet |
| **Phase C (Planned)** | Multi-chain support (Ethereum, Solana, Arbitrum) |

The interface remains the same — `submit_transfer()` and `confirm_transfer()` — so the settlement service requires no changes when switching from simulated to live blockchain operations.

## Chain Configuration

| Variable | Default | Description |
|:---------|:--------|:------------|
| `CHAIN` | `base_sepolia` | Target blockchain network |
| `ASSET` | `USDC` | Stablecoin used for transfers |
| `REQUIRED_CONFIRMATIONS` | `12` | Blocks before tx is considered final |
