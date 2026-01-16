import logging
from decimal import Decimal
from src.core.policy import DataSovereigntyViolation, STATUTORY_MAX_EGRESS_FEE, LegalReference
from src.domain.models import UCPTransaction, AgentIdentity

logger = logging.getLogger("sovereign.firewall")
logging.basicConfig(level=logging.INFO)

class SRENComplianceFilter:
    def __init__(self, cloud_provider_rate_per_gb: Decimal):
        self.rate = cloud_provider_rate_per_gb

    async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction) -> bool:
        logger.info(f"AUDIT START: {tx.intent} | Provider: {agent.provider}")

        if agent.provider == "GOOGLE_UCP" and agent.compliance_score < 0.9:
            logger.warning(f"Low trust score detected for agent {agent.agent_id}")

        # Cost projection
        size_gb = Decimal(str(tx.payload_size_mb)) / Decimal("1024")
        projected_cost = size_gb * self.rate

        # SREN Enforcement (Article 27)
        if projected_cost > STATUTORY_MAX_EGRESS_FEE:
            logger.critical(f"BLOCKING TX {tx.transaction_id}: Cost {projected_cost}EUR exceeds limit.")
            raise DataSovereigntyViolation(
                provider="AWS_LEGACY_TIER",
                cost=projected_cost,
                context=f"UCP Egress via {agent.provider}"
            )

        logger.info(f"COMPLIANT: {LegalReference.ARRETE_EGRESS.value}. ACCESS GRANTED.")
        return True
