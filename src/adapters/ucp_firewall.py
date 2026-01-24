import logging
import decimal
import hashlib
from decimal import Decimal, InvalidOperation
from src.core.policy import (
    DataSovereigntyViolation, 
    STATUTORY_MAX_EGRESS_FEE, 
    EnforcementMode, 
    SRENConfig,
    UCP_PROTOCOL_OVERHEAD
)
from src.domain.models import UCPTransaction, AgentIdentity
from src.ports.billing_provider import BillingProvider

SREN_ENGINE_VERSION = "2026.1.7-platinum"
HASH_ALGO = "sha256"
logger = logging.getLogger("sovereign.firewall")

class SRENComplianceFilter:
    def __init__(self, billing_service: BillingProvider):
        self.billing_service = billing_service

    async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction, config: SRENConfig = SRENConfig()) -> bool:
        tx_id = tx.transaction_id
        secure_hash = hashlib.sha256(tx_id.encode()).hexdigest()[:12]
        
        logger.info(f"AUDIT|v={SREN_ENGINE_VERSION}|tx_hash={HASH_ALGO}:{secure_hash}|prov={agent.provider}")

        try:
            with decimal.localcontext() as ctx:
                ctx.prec = 28
                ctx.rounding = decimal.ROUND_HALF_UP
                
                if tx.payload_size_mb < 0:
                    raise ValueError("NEGATIVE_PAYLOAD")

                current_rate = await self.billing_service.get_current_egress_rate()
                
                size_gb = (tx.payload_size_mb * UCP_PROTOCOL_OVERHEAD) / Decimal("1024")
                projected_cost = (size_gb * current_rate).quantize(Decimal("0.0001"))

            if projected_cost > STATUTORY_MAX_EGRESS_FEE:
                if config.mode == EnforcementMode.STRICT:
                    raise DataSovereigntyViolation(agent.provider, projected_cost, "SREN_BLOCK")
            
            return True

        except (InvalidOperation, ValueError, TypeError) as e:
            logger.error(f"[{tx_id}] VALIDATION_FAILURE: {str(e)}")
            raise DataSovereigntyViolation("INTERNAL", Decimal("0.00"), "INPUT_REJECTION")
        except DataSovereigntyViolation:
            raise
        except Exception as e:
            logger.critical(f"[{tx_id}] KERNEL_PANIC: {str(e)}", exc_info=True)
            raise DataSovereigntyViolation("SYSTEM", Decimal("0.00"), "FAIL_SAFE_SHUTDOWN")
