import logging
import decimal
import hashlib
from importlib.metadata import version, PackageNotFoundError
from decimal import Decimal, InvalidOperation
from src.core.policy import (
    DataSovereigntyViolation, 
    STATUTORY_MAX_EGRESS_FEE, 
    EnforcementMode, 
    SRENConfig,
    create_secure_config
)
from src.domain.models import UCPTransaction, AgentIdentity
from src.ports.billing_provider import BillingProvider

try:
    SREN_ENGINE_VERSION = version("ucp-sovereign-middleware")
except PackageNotFoundError:
    SREN_ENGINE_VERSION = "0.0.0-dev"

logger = logging.getLogger("sovereign.firewall")
ALLOWED_HASH_ALGOS = {"sha256", "sha3_256", "sha3_512", "blake2b"}

class SRENComplianceFilter:
    def __init__(self, billing_service: BillingProvider):
        self.billing_service = billing_service

    def _get_secure_hash(self, tx_id: str, algo: str) -> str:
        if algo not in ALLOWED_HASH_ALGOS:
            logger.critical(f"SECURITY_ALERT: Algo '{algo}' not in allowlist. Fallback to sha256.")
            algo = "sha256"
        try:
            hasher = getattr(hashlib, algo)
            return hasher(tx_id.encode()).hexdigest()[:12]
        except (AttributeError, TypeError) as e:
            logger.error(f"CRYPTO_FAILURE: Algo {algo} instantiation failed: {e}")
            return hashlib.sha256(tx_id.encode()).hexdigest()[:12]

async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction, config: SRENConfig | None = None) -> bool:
        if config is None:
            config = create_secure_config()

        if not config.verify_integrity():
            logger.critical("TAMPERING_DETECTED|Config signature mismatch!")
            raise DataSovereigntyViolation("INTERNAL", Decimal("0.00"), "INTEGRITY_COMPROMISE")

        local_config = config 
        tx_id = tx.transaction_id
        secure_hash = self._get_secure_hash(tx_id, local_config.hash_algorithm)
        
        try:
            return True

        except (InvalidOperation, ValueError, TypeError) as e:
            logger.error(f"[{secure_hash}] VALIDATION_FAILURE: {str(e)}")
            raise DataSovereigntyViolation("INTERNAL", Decimal("0.00"), "INPUT_REJECTION")
        except DataSovereigntyViolation:
            raise
        except Exception as e:
            logger.critical(f"[{secure_hash}] KERNEL_PANIC: {str(e)}", exc_info=True)
            raise DataSovereigntyViolation("SYSTEM", Decimal("0.00"), "FAIL_SAFE_SHUTDOWN")
