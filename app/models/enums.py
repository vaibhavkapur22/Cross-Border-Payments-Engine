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


VALID_TRANSITIONS: dict[TransferStatus, list[TransferStatus]] = {
    TransferStatus.CREATED: [TransferStatus.QUOTED, TransferStatus.FAILED],
    TransferStatus.QUOTED: [TransferStatus.FUNDED, TransferStatus.FAILED],
    TransferStatus.FUNDED: [TransferStatus.USD_TO_USDC_COMPLETE, TransferStatus.FAILED],
    TransferStatus.USD_TO_USDC_COMPLETE: [TransferStatus.ONCHAIN_TRANSFER_PENDING, TransferStatus.FAILED],
    TransferStatus.ONCHAIN_TRANSFER_PENDING: [TransferStatus.ONCHAIN_TRANSFER_CONFIRMED, TransferStatus.FAILED],
    TransferStatus.ONCHAIN_TRANSFER_CONFIRMED: [TransferStatus.USDC_TO_INR_PENDING, TransferStatus.FAILED],
    TransferStatus.USDC_TO_INR_PENDING: [TransferStatus.SETTLED, TransferStatus.FAILED],
    TransferStatus.SETTLED: [TransferStatus.COMPLETED, TransferStatus.FAILED],
    TransferStatus.COMPLETED: [],
    TransferStatus.FAILED: [],
}


class LedgerEntryType(str, Enum):
    FUNDING = "funding"
    FEE_CAPTURE = "fee_capture"
    TREASURY_ALLOCATION = "treasury_allocation"
    PAYOUT_LIABILITY = "payout_liability"
    SETTLEMENT_COMPLETION = "settlement_completion"


class BlockchainTxStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
