from decimal import Decimal
from enum import Enum
from dataclasses import dataclass

STATUTORY_MAX_EGRESS_FEE = Decimal("0.00")
UCP_PROTOCOL_OVERHEAD = Decimal("1.02")

class LegalReference(Enum):
    ARRETE_EGRESS = "NOR:ECOI2530768A"
    LOI_SREN = "LOI n° 2024-449"

class EnforcementMode(Enum):
    STRICT = "strict"
    ADVISORY = "advisory"

@dataclass(frozen=True)
class SRENConfig:
    mode: EnforcementMode = EnforcementMode.STRICT
    allow_value_added_services: bool = False
    hash_algorithm: str = "sha256"
    credit_balance: Decimal = Decimal("0.00")
    network_overhead: Decimal = Decimal("1.02")

class DataSovereigntyViolation(Exception):
    def __init__(self, provider: str, cost: Decimal, reason: str):
        self.provider = provider
        self.cost = cost
        self.reason = reason
        super().__init__(
            f"[VIOLATION] {provider} attempts to charge {cost} EUR/GB. "
            f"Reason: {reason}. Ref: {LegalReference.ARRETE_EGRESS.value}"
        )
