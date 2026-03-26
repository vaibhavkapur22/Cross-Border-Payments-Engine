"""
Comparison Engine — benchmarks the stablecoin route against a SWIFT transfer.

Fee and latency estimates are configurable via settings.
"""

from app.config import settings
from app.models.tables import Quote


def calculate_comparison(source_amount_usd: float, quote: Quote) -> dict:
    """
    Returns a comparison dict with stablecoin and SWIFT route breakdowns.
    """
    # ── Stablecoin route ────────────────────────────────
    stablecoin_fees = {
        "platform_fee": quote.platform_fee,
        "network_fee": quote.network_fee,
        "fx_spread": quote.fx_spread,
        "payout_partner_fee": settings.payout_partner_fee,
    }
    stablecoin_total_fee = round(sum(stablecoin_fees.values()), 2)

    # Latency estimates in seconds
    stablecoin_latency = {
        "funding": 120,          # 2 minutes
        "usd_to_usdc": 30,      # 30 seconds
        "onchain_transfer": 90,  # ~1.5 minutes
        "confirmation": 30,      # 30 seconds
        "offramp_prep": 180,     # 3 minutes
        "local_payout": 300,     # 5 minutes
    }
    stablecoin_total_time = sum(stablecoin_latency.values())  # ~750s ≈ 12.5 min

    # ── SWIFT route ─────────────────────────────────────
    swift_fx_spread = round(source_amount_usd * settings.swift_fx_spread_pct, 2)
    swift_fees = {
        "sender_bank_fee": settings.swift_sender_bank_fee,
        "intermediary_fee": settings.swift_intermediary_fee,
        "receiver_fee": settings.swift_receiver_fee,
        "fx_spread": swift_fx_spread,
    }
    swift_total_fee = round(sum(swift_fees.values()), 2)

    # SWIFT latency: model as 1–24 hours, use midpoint of 4 hours
    swift_total_time = 14400  # 4 hours in seconds

    return {
        "source_amount_usd": source_amount_usd,
        "stablecoin_route": {
            "total_fee_usd": stablecoin_total_fee,
            "estimated_time_seconds": stablecoin_total_time,
            "fee_components": stablecoin_fees,
        },
        "swift_route": {
            "total_fee_usd": swift_total_fee,
            "estimated_time_seconds": swift_total_time,
            "fee_components": swift_fees,
        },
        "fee_savings_usd": round(swift_total_fee - stablecoin_total_fee, 2),
        "time_savings_seconds": swift_total_time - stablecoin_total_time,
    }
