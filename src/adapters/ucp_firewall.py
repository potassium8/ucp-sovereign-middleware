import logging
from decimal import Decimal
from src.core.policy import DataSovereigntyViolation, STATUTORY_MAX_EGRESS_FEE, LegalReference, EnforcementMode, SRENConfig
from src.domain.models import UCPTransaction, AgentIdentity
from src.core.performance import monitor_latency

logger = logging.getLogger("sovereign.firewall")

class SRENComplianceFilter:
    def __init__(self, cloud_provider_rate_per_gb: Decimal):
        self.rate = cloud_provider_rate_per_gb
        self.payload_correction_factor = Decimal("0.98")

    @monitor_latency
    async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction, config: SRENConfig = SRENConfig()) -> bool:
        logger.info(f"AUDIT START: {tx.intent} | Agent: {agent.agent_id}")

        # Anti-fraud: Null or negative payload detection
        if tx.payload_size_mb <= 0:
            logger.warning(f"FRAUD_ALERT: Zero-size payload for TX {tx.transaction_id}")
            if config.mode == EnforcementMode.STRICT:
                raise DataSovereigntyViolation(agent.provider, Decimal("0.01"), "Bypass attempt detected")

        # Semantic Egress Valuation
        size_gb = (Decimal(str(tx.payload_size_mb)) * self.payload_correction_factor) / Decimal("1024")
        projected_cost = size_gb * self.rate

        if projected_cost > STATUTORY_MAX_EGRESS_FEE:
            msg = f"SREN_VIOLATION: {projected_cost} EUR exceeds statutory limit"
            if config.mode == EnforcementMode.STRICT:
                logger.critical(msg)
                raise DataSovereigntyViolation(agent.provider, projected_cost, "Strict Enforcement")
            
            logger.warning(f"[ADVISORY] {msg}. Proceeding under value-added flag.")

        logger.info(f"COMPLIANT: {tx.transaction_id} cleared via {LegalReference.ARRETE_EGRESS.value}")
        return True
