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
        self.metrics = {"violations": 0, "total_audits": 0}

    @monitor_latency
    async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction, config: SRENConfig = SRENConfig()) -> bool:
        self.metrics["total_audits"] += 1
        tx_id = tx.transaction_id
        logger.info(f"[{tx_id}] AUDIT_START | Agent: {agent.agent_id} | Provider: {agent.provider}")

        if tx.payload_size_mb <= 0:
            logger.warning(f"[{tx_id}] FRAUD_ALERT: Zero or negative payload")
            if config.mode == EnforcementMode.STRICT:
                raise DataSovereigntyViolation(agent.provider, Decimal("0.01"), "Null-payload bypass attempt")

        try:
            current_rate = await self.billing_service.get_current_egress_rate()
        except Exception as e:
            logger.error(f"[{tx_id}] BILLING_SERVICE_ERROR: {str(e)}")
            raise DataSovereigntyViolation(agent.provider, Decimal("0.00"), "Billing API failure - Safety block")

        size_gb = (Decimal(str(tx.payload_size_mb)) * self.payload_correction_factor) / Decimal("1024")
        projected_cost = size_gb * current_rate

        if projected_cost > STATUTORY_MAX_EGRESS_FEE:
            self.metrics["violations"] += 1
            msg = f"SREN_VIOLATION: {projected_cost} EUR exceeds limit (Rate: {current_rate}/GB)"
            if config.mode == EnforcementMode.STRICT:
                logger.critical(f"[{tx_id}] {msg}")
                raise DataSovereigntyViolation(agent.provider, projected_cost, "Strict Enforcement")
            logger.warning(f"[{tx_id}] [ADVISORY] {msg}")

        logger.info(f"[{tx_id}] COMPLIANT: Cleared via {LegalReference.ARRETE_EGRESS.value}")
        return True
