import logging
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

SREN_ENGINE_VERSION = "2026.1.4-gold"
logger = logging.getLogger("sovereign.firewall")

class SRENComplianceFilter:
    def __init__(self, billing_service: BillingProvider):
        self.billing_service = billing_service
        self.metrics = {"violations": 0, "total_audits": 0}

    async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction, config: SRENConfig = SRENConfig()) -> bool:
        self.metrics["total_audits"] += 1
        tx_id = tx.transaction_id
        
        audit_context = {
            "v": SREN_ENGINE_VERSION,
            "tx": tx_id,
            "agent": agent.agent_id,
            "net": getattr(agent, "region", "EU-DEFAULT")
        }
        logger.info(f"AUDIT_RECORD|{audit_context}")

        try:
            raw_size = tx.payload_size_mb
            if not isinstance(raw_size, (int, float, Decimal)) or raw_size > 1_000_000:
                raise ValueError("SIZE_EXCESSIVE_OR_INVALID")

            current_rate = await self.billing_service.get_current_egress_rate()
            size_gb = (Decimal(str(raw_size)) * UCP_PROTOCOL_OVERHEAD) / Decimal("1024")
            projected_cost = size_gb * current_rate

            if projected_cost > STATUTORY_MAX_EGRESS_FEE:
                self.metrics["violations"] += 1
                if config.mode == EnforcementMode.STRICT:
                    raise DataSovereigntyViolation(agent.provider, projected_cost, "SREN_COST_LIMIT")
            
            return True

        except (InvalidOperation, ValueError) as e:
            logger.error(f"[{tx_id}] VALIDATION_ERROR: {str(e)}")
            raise DataSovereigntyViolation("VALIDATION", Decimal("0.00"), "MALFORMED_TX")
        except Exception as e:
            logger.critical(f"[{tx_id}] ENGINE_FAULT: {str(e)}")
            raise DataSovereigntyViolation("SYSTEM", Decimal("0.00"), "FAIL_SAFE_LOCK")
