import uuid
from datetime import datetime, timezone

from app.models.tables import BlockchainTransaction


def simulate_usdc_transfer(transfer_id: str, amount: float) -> BlockchainTransaction:
    """
    Create a simulated USDC transfer (Mode A: fully simulated).
    Generates a fake tx hash and wallet addresses.
    """
    tx_hash = "0x" + uuid.uuid4().hex + uuid.uuid4().hex[:24]
    from_addr = "0x" + uuid.uuid4().hex[:40]
    to_addr = "0x" + uuid.uuid4().hex[:40]

    return BlockchainTransaction(
        transfer_id=transfer_id,
        chain="base_sepolia",
        asset="USDC",
        amount=amount,
        from_address=from_addr,
        to_address=to_addr,
        tx_hash=tx_hash,
        confirmations=0,
        status="pending",
        submitted_at=datetime.now(timezone.utc),
    )


def simulate_confirmation(tx: BlockchainTransaction) -> BlockchainTransaction:
    """Simulate a blockchain confirmation."""
    tx.confirmations = 12
    tx.status = "confirmed"
    tx.confirmed_at = datetime.now(timezone.utc)
    return tx
