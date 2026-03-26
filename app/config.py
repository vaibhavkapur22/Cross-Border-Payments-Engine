from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./cross_border.db"
    database_url_sync: str = "sqlite:///./cross_border.db"
    redis_url: str = "redis://localhost:6379/0"

    # FX defaults
    usd_inr_mid_rate: float = 83.20
    stablecoin_fx_spread_pct: float = 0.004
    swift_fx_spread_pct: float = 0.018

    # Fee defaults (USD)
    platform_fee: float = 1.50
    network_fee: float = 0.35
    payout_partner_fee: float = 0.75

    # SWIFT fee estimates (USD)
    swift_sender_bank_fee: float = 15.00
    swift_intermediary_fee: float = 8.00
    swift_receiver_fee: float = 5.00

    # Quote TTL in seconds
    quote_ttl_seconds: int = 300

    model_config = {"env_file": ".env"}


settings = Settings()
