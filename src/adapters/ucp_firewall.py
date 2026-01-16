import logging
from decimal import Decimal
from src.core.policy import DataSovereigntyViolation, STATUTORY_MAX_EGRESS_FEE, LegalReference, EnforcementMode, SRENConfig
from src.domain.models import UCPTransaction, AgentIdentity
from src.core.performance import monitor_latency
from src.ports.billing_provider import BillingProvider

logger = logging.getLogger("sovereign.firewall")

class SRENComplianceFilter:
    def __init__(self, billing_service: BillingProvider):
        
        self.billing_service = billing_service
        self.payload_correction_factor = Decimal("0.98")

    @monitor_latency
    async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction, config: SRENConfig = SRENConfig()) -> bool:
        tx_id = tx.transaction_id
        logger.info(f"[{tx_id}] AUDIT START | Agent: {agent.agent_id}")

        if tx.payload_size_mb <= 0:
            logger.warning(f"[{tx_id}] FRAUD_ALERT: Zero-size payload detected")
            if config.mode == EnforcementMode.STRICT:
                raise DataSovereigntyViolation(agent.provider, Decimal("0.01"), "Bypass attempt")

        current_rate = await self.billing_service.get_current_egress_rate()
        
        size_gb = (Decimal(str(tx.payload_size_mb)) * self.payload_correction_factor) / Decimal("1024")
        projected_cost = size_gb * current_rate

        if projected_cost > STATUTORY_MAX_EGRESS_FEE:
            msg = f"SREN_VIOLATION: {projected_cost} EUR exceeds limit (Rate: {current_rate}/GB)"
            if config.mode == EnforcementMode.STRICT:
                logger.critical(f"[{tx_id}] {msg}")
                raise DataSovereigntyViolation(agent.provider, projected_cost, "Strict Enforcement")
            logger.warning(f"[{tx_id}] [ADVISORY] {msg}")

        logger.info(f"[{tx_id}] COMPLIANT: Cleared via {LegalReference.ARRETE_EGRESS.value}")
        return True
