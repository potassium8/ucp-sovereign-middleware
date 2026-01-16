import logging
from decimal import Decimal
from src.core.policy import DataSovereigntyViolation, STATUTORY_MAX_EGRESS_FEE, EnforcementMode, SRENConfig, LegalReference
from src.domain.models import UCPTransaction, AgentIdentity
from src.ports.billing_provider import BillingProvider

logger = logging.getLogger("sovereign.firewall")

class SRENComplianceFilter:
    def __init__(self, billing_service: BillingProvider):
        self.billing_service = billing_service
        self.payload_correction_factor = Decimal("0.98")
        self.metrics = {"violations": 0, "total_audits": 0}

    async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction, config: SRENConfig = SRENConfig()) -> bool:
        self.metrics["total_audits"] += 1
        tx_id = tx.transaction_id
        
        logger.info(f"AUDIT_RECORD|{tx_id}|{agent.agent_id}|{agent.provider}|{getattr(agent, 'region', 'EU-DEFAULT')}")

        try:
            if hasattr(agent, 'region') and not agent.region.startswith("eu-"):
                logger.warning(f"[{tx_id}] GEO_RISK: {agent.region}")

            current_rate = await self.billing_service.get_current_egress_rate()
            size_gb = (Decimal(str(tx.payload_size_mb)) * self.payload_correction_factor) / Decimal("1024")
            projected_cost = size_gb * current_rate

            if projected_cost > STATUTORY_MAX_EGRESS_FEE:
                self.metrics["violations"] += 1
                if config.mode == EnforcementMode.STRICT:
                    raise DataSovereigntyViolation(agent.provider, projected_cost, "SREN_COST_VIOLATION")
            
            return True

        except DataSovereigntyViolation:
            raise
        except Exception as e:
            logger.critical(f"[{tx_id}] FAIL_SAFE_LOCK: {str(e)}")
            raise DataSovereigntyViolation("SYSTEM", Decimal("0.00"), "PROTECTION_LOCK_ON_FAILURE")
