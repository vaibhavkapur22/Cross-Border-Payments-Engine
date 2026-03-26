# Cross-border Payments Engine

## Project Summary

Build a **cross-border stablecoin payments engine** that simulates a **US → India transfer** using **USDC** as the settlement rail.

Core capabilities:
- USD → USDC conversion simulation
- Onchain USDC transfer
- USDC → INR settlement simulation
- end-to-end settlement tracking
- fee comparison vs SWIFT
- latency comparison vs SWIFT

This project should feel like a real **stablecoin infrastructure / remittance backend** rather than just a crypto demo.

---

## 1. Product Goal

### User story
A US business wants to send money to a recipient in India.

The engine should:
1. accept a transfer request in USD,
2. quote FX and fees,
3. simulate conversion from USD to USDC,
4. move value using USDC,
5. simulate off-ramp conversion into INR,
6. track the transfer through each settlement stage,
7. compare the route against a SWIFT-style transfer on cost and speed.

### Why this project is strong
This demonstrates:
- payments orchestration
- ledger and balances design
- FX quoting
- async workflows and settlement state machines
- blockchain integration
- benchmarking against incumbent rails
- realistic payment infrastructure thinking

---

## 2. Scope for MVP

### Build in MVP
- quote generation
- transfer creation
- simulated USD funding
- simulated USD → USDC treasury conversion
- testnet or simulated USDC transfer
- simulated USDC → INR off-ramp
- settlement timeline and status tracking
- ledger entries
- fee comparison vs SWIFT
- latency comparison vs SWIFT

### Do not build first
- real US bank integrations
- real India bank payout rails
- production custody
- full KYC / AML stack
- real FX provider integration
- production compliance workflows

The first version should be **simulation-heavy but infra-realistic**.

---

## 3. Recommended Tech Stack

### Backend
- **Python + FastAPI**

### Database
- **Postgres**

### Async / background jobs
- **Redis + Celery** or FastAPI background workers

### Blockchain layer
- **Base Sepolia** or **Ethereum Sepolia**

### Frontend (optional initially)
- **React** dashboard for transfer tracking

### Local development
- **Docker Compose**

### Suggested project structure
```text
cross-border-engine/
  app/
    api/
    services/
    models/
    workers/
    ledger/
    blockchain/
    fx/
    comparison/
  migrations/
  tests/
  scripts/
  docker-compose.yml
  README.md
```

---

## 4. High-Level Architecture

Break the system into six logical components.

### 4.1 Payment API Service
Receives transfer and quote requests.

Responsibilities:
- validate incoming requests
- create quotes
- create transfers
- return transfer status
- expose transfer timeline

### 4.2 FX and Quote Engine
Calculates:
- USD → USDC conversion
- USDC → INR conversion
- FX spread
- fees
- target INR estimate

Use a mock or configurable FX model for MVP.

### 4.3 Wallet and Blockchain Service
Responsibilities:
- create or manage treasury / sender / recipient wallets
- submit USDC transfer (real testnet or simulated)
- poll for confirmations
- persist tx hash and chain metadata

### 4.4 Settlement Workflow Engine
Manages transfer lifecycle:
- created
- quoted
- funded
- usd_to_usdc_complete
- onchain_transfer_pending
- onchain_transfer_confirmed
- usdc_to_inr_pending
- settled
- completed
- failed

This should be event-driven.

### 4.5 Ledger Service
Tracks movement of value internally using ledger entries.

Responsibilities:
- record funding
- record fee capture
- record treasury movement
- record payout liability
- record settlement completion

### 4.6 Benchmark / Comparison Service
Calculates:
- stablecoin route fee estimate
- stablecoin route latency estimate
- SWIFT fee estimate
- SWIFT latency estimate

---

## 5. End-to-End Transfer Flow

### Step 1: Create quote
Client requests a quote.

Example:
```json
POST /quotes
{
  "source_currency": "USD",
  "target_currency": "INR",
  "amount": 500.00,
  "source_country": "US",
  "target_country": "IN"
}
```

Example response:
```json
{
  "quote_id": "qt_123",
  "source_amount_usd": 500.00,
  "fx_rate_usd_inr": 83.20,
  "platform_fee_usd": 1.50,
  "network_fee_usd": 0.35,
  "fx_spread_usd": 2.00,
  "recipient_amount_inr": 41332.80,
  "expires_at": "2026-03-26T15:05:00Z"
}
```

### Step 2: Create transfer
Client confirms the transfer using a quote.

```json
POST /transfers
{
  "quote_id": "qt_123",
  "recipient": {
    "name": "Aarav Sharma",
    "bank_account_hint": "xxxx1234"
  },
  "route_preference": "lowest_cost"
}
```

### Step 3: Simulate sender funding
For MVP, mark the transfer as funded after request acceptance or via an admin action.

### Step 4: Convert USD to USDC
Treasury layer simulates moving USD value into USDC inventory.

### Step 5: Transfer USDC onchain
Either:
- submit a real testnet transfer, or
- simulate the transfer and confirmations.

### Step 6: Convert USDC to INR
Simulate an India payout partner converting USDC value into INR.

### Step 7: Settle recipient
Mark payout completed and persist final amount, timestamps, and references.

---

## 6. Transfer Lifecycle / State Machine

Use a clear state machine.

```python
from enum import Enum

class TransferStatus(str, Enum):
    CREATED = "created"
    QUOTED = "quoted"
    FUNDED = "funded"
    USD_TO_USDC_COMPLETE = "usd_to_usdc_complete"
    ONCHAIN_TRANSFER_PENDING = "onchain_transfer_pending"
    ONCHAIN_TRANSFER_CONFIRMED = "onchain_transfer_confirmed"
    USDC_TO_INR_PENDING = "usdc_to_inr_pending"
    SETTLED = "settled"
    COMPLETED = "completed"
    FAILED = "failed"
```

Suggested transitions:
- `created -> quoted`
- `quoted -> funded`
- `funded -> usd_to_usdc_complete`
- `usd_to_usdc_complete -> onchain_transfer_pending`
- `onchain_transfer_pending -> onchain_transfer_confirmed`
- `onchain_transfer_confirmed -> usdc_to_inr_pending`
- `usdc_to_inr_pending -> settled`
- `settled -> completed`
- any state can move to `failed`

---

## 7. Data Model

### 7.1 `quotes`
```sql
id
source_currency
target_currency
source_amount
fx_rate
fx_source
platform_fee
network_fee
fx_spread
estimated_target_amount
expires_at
created_at
```

### 7.2 `transfers`
```sql
id
quote_id
sender_id
recipient_id
source_currency
target_currency
source_amount
target_amount_estimated
target_amount_final
route_type
status
created_at
updated_at
completed_at
```

### 7.3 `wallets`
```sql
id
owner_type
owner_id
chain
address
custody_provider
created_at
```

### 7.4 `blockchain_transactions`
```sql
id
transfer_id
chain
asset
amount
from_address
to_address
tx_hash
confirmations
status
submitted_at
confirmed_at
```

### 7.5 `ledger_entries`
```sql
id
transfer_id
entry_type
account_debit
account_credit
amount
currency
created_at
```

### 7.6 `settlement_events`
```sql
id
transfer_id
event_type
payload_json
created_at
```

### 7.7 `benchmarks`
```sql
id
transfer_id
stablecoin_total_fee
stablecoin_total_time_sec
swift_estimated_fee
swift_estimated_time_sec
created_at
```

---

## 8. API Design

### Quotes
```http
POST /quotes
GET /quotes/{id}
```

### Transfers
```http
POST /transfers
GET /transfers/{id}
GET /transfers/{id}/timeline
```

### Webhooks
```http
POST /webhooks/blockchain
POST /webhooks/settlement
```

### Comparison
```http
GET /transfers/{id}/comparison
```

### Admin / simulation helpers
```http
POST /admin/transfers/{id}/advance
POST /admin/transfers/{id}/fail
```

---

## 9. FX Model

Use a configurable FX model in MVP.

Example assumptions:
- mid-market USD/INR = 83.20
- stablecoin route spread = 0.40%
- SWIFT route spread = 1.80%

### Example quote logic
```python
def calculate_quote(source_amount_usd: float, usd_inr_rate: float) -> dict:
    platform_fee = 1.50
    network_fee = 0.35
    fx_spread_pct = 0.004

    spread_cost = source_amount_usd * fx_spread_pct
    net_usd = source_amount_usd - platform_fee - network_fee - spread_cost
    recipient_inr = net_usd * usd_inr_rate

    return {
        "platform_fee": platform_fee,
        "network_fee": network_fee,
        "fx_spread": round(spread_cost, 2),
        "recipient_amount_inr": round(recipient_inr, 2),
    }
```

Later you can swap in a real FX API.

---

## 10. Fee Comparison Model

### Stablecoin route fees
Include:
- platform fee
- network fee
- FX spread
- payout partner fee

Example:
- platform fee = $1.50
- network fee = $0.20
- FX spread = $2.10
- payout partner fee = $0.75
- **total = $4.55**

### SWIFT route estimate
Include:
- sender bank fee
- intermediary/correspondent fee estimate
- receiver bank fee estimate
- FX spread

Example:
- sender bank fee = $15
- intermediary fee = $8
- receiver fee = $5
- FX spread = $9
- **total = $37**

Model SWIFT as an **estimate**, not as exact reality.

---

## 11. Latency Comparison Model

### Stablecoin route example
- funding = 2 minutes
- USD → USDC conversion = 30 seconds
- onchain transfer = 15 seconds to 2 minutes
- confirmation threshold = 30 seconds
- off-ramp payout prep = 3 minutes
- local payout completion = 5 minutes
- **total ≈ 10 minutes**

### SWIFT estimate example
- payment initiation = immediate
- bank/correspondent handling = variable
- compliance checks = variable
- beneficiary credit = variable
- **total ≈ 30 minutes to 24 hours**

Important positioning:
- onchain settlement can be very fast,
- end-user delivery still depends on fiat endpoints and payout infrastructure.

---

## 12. Ledger Design

The ledger is what makes the project feel payments-grade.

### Example entries when transfer is funded
```text
DR Cash_USD_Omnibus                500.00 USD
CR Customer_Funding_Liability      500.00 USD
```

### Example entries when fees are recognized
```text
DR Customer_Funding_Liability        1.50 USD
CR Platform_Fee_Revenue              1.50 USD
```

### Example entries when USDC treasury is allocated
```text
DR USDC_Treasury_Asset             498.50 USD
CR Customer_Funding_Liability      498.50 USD
```

### Example entries when recipient liability is settled
```text
DR Recipient_Payout_Liability      xxxx INR
CR India_Settlement_Clearing       xxxx INR
```

Keep the first version simple but structured.

---

## 13. Blockchain Integration Strategy

Use one of two modes.

### Mode A: Fully simulated
- no real chain calls
- generate tx hashes
- simulate confirmations
- easiest for fast MVP

### Mode B: Hybrid realistic mode
- use real testnet wallets
- submit real testnet token transfers
- keep fiat on/off-ramp simulated
- best for credibility

Recommended: start with Mode A, then upgrade to Mode B.

### Store blockchain metadata
Persist:
- chain
- token
- sender address
- recipient address
- tx hash
- explorer URL
- submitted timestamp
- confirmed timestamp
- number of confirmations

---

## 14. Async Workflow and Events

Make the workflow event-driven.

Suggested events:
- `transfer.created`
- `transfer.quoted`
- `transfer.funded`
- `treasury.usd_to_usdc.completed`
- `blockchain.tx_submitted`
- `blockchain.tx_confirmed`
- `settlement.initiated`
- `settlement.completed`
- `transfer.failed`

Each event should:
- be stored in `settlement_events`
- be visible in a timeline API
- optionally trigger a webhook to clients

---

## 15. Workflow Service Pseudocode

```python
def process_transfer(transfer_id: str):
    transfer = repo.get_transfer(transfer_id)

    if transfer.status == "funded":
        treasury.convert_usd_to_usdc(transfer)
        repo.update_status(transfer_id, "usd_to_usdc_complete")
        events.publish("treasury.usd_to_usdc.completed", transfer_id)

    if transfer.status == "usd_to_usdc_complete":
        tx = blockchain.send_usdc(transfer)
        repo.save_blockchain_tx(transfer_id, tx)
        repo.update_status(transfer_id, "onchain_transfer_pending")
        events.publish("blockchain.tx_submitted", transfer_id)
```

A blockchain confirmation worker can then update:
- `onchain_transfer_pending -> onchain_transfer_confirmed`

A settlement worker can then update:
- `onchain_transfer_confirmed -> usdc_to_inr_pending -> settled -> completed`

---

## 16. What to Show in the UI

A strong transfer detail page should show:
- sender amount in USD
- recipient amount in INR
- FX rate used
- route: USD → USDC → INR
- chain used
- tx hash
- current transfer status
- chronological event timeline
- fee breakdown
- latency breakdown
- stablecoin vs SWIFT comparison card

### Example cards
**Stablecoin route**
- Total fee: $4.55
- Estimated delivery: 8m 42s
- Onchain confirmation: 21s

**SWIFT estimate**
- Total fee: $32.00
- Estimated delivery: 4h–24h

---

## 17. Engineering Quality Features

### Idempotency
Support idempotency for transfer creation:
```http
Idempotency-Key: abc123
```

### Retries
If blockchain submission fails:
- retry up to 3 times
- then move to `manual_review_required` or `failed`

### Reconciliation job
Create a scheduled reconciliation job to verify every completed transfer has:
- a quote
- ledger entries
- blockchain record
- settlement record

### Webhooks
Emit webhooks such as:
- `transfer.processing`
- `transfer.confirmed`
- `transfer.completed`
- `transfer.failed`

### Observability
Add:
- structured logs
- trace ID / correlation ID per transfer
- metrics counters for success / failure / avg settlement time

---

## 18. Phased Delivery Plan

### Phase 1: Pure simulator
Build:
- quote engine
- transfer API
- state machine
- fee model
- FX model
- comparison engine
- ledger entries

Goal: prove architecture and workflow design.

### Phase 2: Real onchain leg
Add:
- wallet creation
- real testnet transfers
- tx confirmation polling
- explorer links

Goal: prove blockchain rail integration.

### Phase 3: Async realism
Add:
- background workers
- event publishing
- webhooks
- retries
- failure modes

Goal: prove payments orchestration maturity.

### Phase 4: Smarter routing
Add:
- multiple chain options
- route optimization by fee / speed / reliability
- corridor-specific pricing and timing

Goal: move toward a true payments router.

---

## 19. Suggested Weekly Build Plan

### Week 1
- initialize FastAPI app
- create Postgres schema
- implement `/quotes`
- implement `/transfers`
- implement simple FX and fee engine

### Week 2
- implement transfer state machine
- add settlement events table
- add background workers
- add ledger posting

### Week 3
- integrate blockchain layer
- create wallets
- simulate or submit testnet transfer
- persist tx metadata
- build confirmation polling

### Week 4
- implement comparison engine
- implement timeline endpoint
- build minimal dashboard or transfer detail UI

### Week 5
- add webhooks
- add retries and failure simulation
- add reconciliation script
- polish README and architecture diagrams
- record demo flow

---

## 20. Stretch Goals

### 20.1 Multi-chain routing
Choose among:
- Base
- Ethereum
- Solana
- SWIFT-estimated route

Based on:
- cheapest
- fastest
- most reliable

### 20.2 Corridor-specific configuration
Support:
- US → India
- US → Mexico
- US → Philippines

with different fees and payout assumptions.

### 20.3 Treasury management
Track balances in:
- USD
- USDC
- INR payable

### 20.4 Compliance hooks
Simulate:
- sanctions check
- transaction amount threshold review
- suspicious velocity flags

### 20.5 Merchant platform layer
Add:
- API keys
- merchant authentication
- list transfers by merchant
- merchant-specific webhook endpoints

---

## 21. How to Position This Project

Use language like this in interviews:

> I built a cross-border payments engine that simulates a USD-to-India remittance using USDC as the settlement rail. The system quotes FX, models fees, executes or simulates the onchain transfer leg, tracks settlement state asynchronously, posts ledger entries, and benchmarks the stablecoin route against a SWIFT-style transfer in terms of cost and latency.

That highlights:
- infra design
- money movement systems
- async orchestration
- blockchain integration
- real-world payments tradeoffs

---

## 22. Best Demo Script

A strong demo should show:
1. create a quote for $500 from US to India
2. show estimated fees and INR output
3. confirm the transfer
4. show funding step
5. show onchain tx pending
6. show tx confirmed
7. show payout settlement complete
8. show stablecoin vs SWIFT comparison

Make the timeline visible and easy to understand.

---

## 23. Recommended Build Order

Build in this order:
1. simulation-first backend
2. internal ledger
3. transfer timeline
4. comparison engine
5. real testnet onchain leg
6. webhooks and retries
7. optional dashboard

This order gives you a working and demonstrable system quickly while keeping the architecture extensible.

---

## 24. Final Principle

Do not pitch this as “stablecoins always beat SWIFT.”

The better framing is:
- stablecoins make settlement more programmable,
- can often reduce cost,
- can improve transparency and speed,
- but total delivery still depends heavily on fiat endpoints, payout partners, and local banking rails.

That nuance makes the project much more credible and realistic.
