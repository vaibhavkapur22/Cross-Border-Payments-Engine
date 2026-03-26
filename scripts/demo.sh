#!/usr/bin/env bash
# ──────────────────────────────────────────────────────
# End-to-end demo: Create a $500 USD→INR transfer,
# advance it through all settlement stages, and view
# the comparison against SWIFT.
# ──────────────────────────────────────────────────────

BASE_URL="${1:-http://localhost:8000}"

set -e

echo "=== 1. Create Quote ==="
QUOTE=$(curl -s -X POST "$BASE_URL/quotes" \
  -H "Content-Type: application/json" \
  -d '{
    "source_currency": "USD",
    "target_currency": "INR",
    "amount": 500.00,
    "source_country": "US",
    "target_country": "IN"
  }')
echo "$QUOTE" | python3 -m json.tool
QUOTE_ID=$(echo "$QUOTE" | python3 -c "import sys,json; print(json.load(sys.stdin)['quote_id'])")

echo ""
echo "=== 2. Create Transfer ==="
TRANSFER=$(curl -s -X POST "$BASE_URL/transfers" \
  -H "Content-Type: application/json" \
  -d "{
    \"quote_id\": \"$QUOTE_ID\",
    \"recipient\": {
      \"name\": \"Aarav Sharma\",
      \"bank_account_hint\": \"xxxx1234\"
    },
    \"route_preference\": \"lowest_cost\"
  }")
echo "$TRANSFER" | python3 -m json.tool
TRANSFER_ID=$(echo "$TRANSFER" | python3 -c "import sys,json; print(json.load(sys.stdin)['transfer_id'])")

echo ""
echo "=== 3. Advance Through All Settlement Stages ==="
RESULT=$(curl -s -X POST "$BASE_URL/admin/transfers/$TRANSFER_ID/advance-all")
echo "$RESULT" | python3 -m json.tool

echo ""
echo "=== 4. Transfer Timeline ==="
curl -s "$BASE_URL/transfers/$TRANSFER_ID/timeline" | python3 -m json.tool

echo ""
echo "=== 5. Ledger Entries ==="
curl -s "$BASE_URL/transfers/$TRANSFER_ID/ledger" | python3 -m json.tool

echo ""
echo "=== 6. Stablecoin vs SWIFT Comparison ==="
curl -s "$BASE_URL/transfers/$TRANSFER_ID/comparison" | python3 -m json.tool

echo ""
echo "=== 7. Final Transfer State ==="
curl -s "$BASE_URL/transfers/$TRANSFER_ID" | python3 -m json.tool
