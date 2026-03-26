from datetime import datetime, timezone, timedelta

from app.config import settings


def get_fx_rate(source: str = "USD", target: str = "INR") -> float:
    """Return the mid-market FX rate. Swap in a real API later."""
    if source == "USD" and target == "INR":
        return settings.usd_inr_mid_rate
    raise ValueError(f"Unsupported currency pair: {source}/{target}")


def calculate_quote(source_amount_usd: float) -> dict:
    """
    Calculate a full quote for a USD→INR stablecoin transfer.

    Returns all fee components and the estimated INR the recipient receives.
    """
    fx_rate = get_fx_rate("USD", "INR")
    platform_fee = settings.platform_fee
    network_fee = settings.network_fee
    fx_spread = round(source_amount_usd * settings.stablecoin_fx_spread_pct, 2)

    net_usd = source_amount_usd - platform_fee - network_fee - fx_spread
    recipient_inr = round(net_usd * fx_rate, 2)

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.quote_ttl_seconds)

    return {
        "source_amount_usd": source_amount_usd,
        "fx_rate": fx_rate,
        "fx_source": "mock",
        "platform_fee": platform_fee,
        "network_fee": network_fee,
        "fx_spread": fx_spread,
        "recipient_amount_inr": recipient_inr,
        "expires_at": expires_at,
    }
