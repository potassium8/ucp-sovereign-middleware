import logging
from decimal import Decimal
from src.core.policy import DataSovereigntyViolation, STATUTORY_MAX_EGRESS_FEE, LegalReference
from src.domain.models import UCPTransaction, AgentIdentity
from src.core.performance import monitor_latency

logger = logging.getLogger("sovereign.firewall")
logging.basicConfig(level=logging.INFO)

class SRENComplianceFilter:
    def __init__(self, cloud_provider_rate_per_gb: Decimal):
        self.rate = cloud_provider_rate_per_gb
        # Correcteur spécifique UCP 1.0 pour isoler le payload réel des overheads
        self.payload_correction_factor = Decimal("0.98")

    @monitor_latency
    async def audit_transaction(self, agent: AgentIdentity, tx: UCPTransaction) -> bool:
        logger.info(f"AUDIT START: {tx.intent} | Provider: {agent.provider}")

        # Data Egress Calculation with semantic correction
        corrected_size = Decimal(str(tx.payload_size_mb)) * self.payload_correction_factor
        size_gb = corrected_size / Decimal("1024")
        projected_cost = size_gb * self.rate

        if projected_cost > STATUTORY_MAX_EGRESS_FEE:
            logger.critical(f"BLOCKING TX {tx.transaction_id}: Cost {projected_cost}EUR exceeds limit.")
            raise DataSovereigntyViolation(
                provider="AWS_LEGACY_TIER",
                cost=projected_cost,
                context=f"UCP Egress via {agent.provider}"
            )

        logger.info(f"COMPLIANT: {LegalReference.ARRETE_EGRESS.value}. ACCESS GRANTED.")
        return True
