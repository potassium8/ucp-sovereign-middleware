import logging
import decimal
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
logger = logging.getLogger("sovereign.firewall")

class SRENComplianceFilter:
    def __init__(self, billing_service: BillingProvider):
        self.billing_service = billing_service

    async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction, config: SRENConfig = SRENConfig()) -> bool:
        tx_id = tx.transaction_id
        
        logger.info(f"AUDIT_EVENT|v={SREN_ENGINE_VERSION}|tx={tx_id}|agent={agent.agent_id}|reg={getattr(agent, 'region', 'EU-DEFAULT')}")

        try:
            if not isinstance(tx.payload_size_mb, (int, float, Decimal)):
                raise TypeError("NON_NUMERIC_PAYLOAD")
            
            with decimal.localcontext() as ctx:
                ctx.prec = 28
                ctx.rounding = decimal.ROUND_HALF_UP
                
                raw_val = Decimal(str(tx.payload_size_mb))
                if raw_val < 0 or raw_val > 1_000_000_000:
                    raise ValueError("OUT_OF_BOUNDS_PAYLOAD")

                current_rate = await self.billing_service.get_current_egress_rate()
                size_gb = (raw_val * UCP_PROTOCOL_OVERHEAD) / Decimal("1024")
                projected_cost = (size_gb * current_rate).quantize(Decimal("0.0001"))

            if projected_cost > STATUTORY_MAX_EGRESS_FEE:
                if config.mode == EnforcementMode.STRICT:
                    raise DataSovereigntyViolation(agent.provider, projected_cost, "SREN_COST_VIOLATION")
                logger.warning(f"[{tx_id}] ADVISORY_BREACH|cost={projected_cost}")
            
            return True

        except (InvalidOperation, ValueError, TypeError) as e:
            logger.error(f"[{tx_id}] VALIDATION_CRITICAL: {str(e)}")
            raise DataSovereigntyViolation("VALIDATION", Decimal("0.00"), "SECURITY_INPUT_REJECTION")
        except DataSovereigntyViolation:
            raise
        except Exception as e:
            logger.critical(f"[{tx_id}] KERNEL_PANIC: {str(e)}", exc_info=True)
            raise DataSovereigntyViolation("SYSTEM", Decimal("0.00"), "FAIL_SAFE_SHUTDOWN")
