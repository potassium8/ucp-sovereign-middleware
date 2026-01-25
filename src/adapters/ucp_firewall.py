import logging
import decimal
import hashlib
from importlib.metadata import version, PackageNotFoundError
from decimal import Decimal, InvalidOperation
from src.core.policy import (
    DataSovereigntyViolation, 
    STATUTORY_MAX_EGRESS_FEE, 
    EnforcementMode, 
    SRENConfig
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
        """
        Loads hashing algo safely via allowlist validation.
        """
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
            config = SRENConfig()

        tx_id = tx.transaction_id
        secure_hash = self._get_secure_hash(tx_id, config.hash_algorithm)
        
        logger.info(f"AUDIT|v={SREN_ENGINE_VERSION}|tx_hash={config.hash_algorithm}:{secure_hash}|prov={agent.provider}")

        try:
            with decimal.localcontext() as ctx:
                ctx.prec = 28
                ctx.rounding = decimal.ROUND_HALF_UP
                
                if tx.payload_size_mb < 0:
                    raise ValueError("NEGATIVE_PAYLOAD")

                current_rate = await self.billing_service.get_current_egress_rate()
                
                size_gb = (tx.payload_size_mb * config.network_overhead) / Decimal("1024")
                projected_cost = (size_gb * current_rate).quantize(Decimal("0.0001"))

            effective_cost = max(Decimal("0.00"), projected_cost - config.credit_balance)

            if effective_cost > STATUTORY_MAX_EGRESS_FEE:
                logger.warning(
                    f"SOVEREIGN_SAVINGS|amount_eur={effective_cost}|provider={agent.provider}|"
                    f"reason=SREN_PREVENTED|ref=NOR:ECOI2530768A"
                )
                
                if config.mode == EnforcementMode.STRICT:
                    raise DataSovereigntyViolation(agent.provider, effective_cost, "SREN_BLOCK")
            
            return True

        except (InvalidOperation, ValueError, TypeError) as e:
            logger.error(f"[{secure_hash}] VALIDATION_FAILURE: {str(e)}")
            raise DataSovereigntyViolation("INTERNAL", Decimal("0.00"), "INPUT_REJECTION")
        except DataSovereigntyViolation:
            raise
        except Exception as e:
            logger.critical(f"[{secure_hash}] KERNEL_PANIC: {str(e)}", exc_info=True)
            raise DataSovereigntyViolation("SYSTEM", Decimal("0.00"), "FAIL_SAFE_SHUTDOWN")
