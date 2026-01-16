from enum import Enum
from decimal import Decimal
from typing import Final
from pydantic import BaseModel

class LegalReference(Enum):
    SREN_ART_27 = "LOI_2024_449_ART_27"
    ARRETE_EGRESS = "NOR_ECOI2530768A"

class EnforcementMode(Enum):
    STRICT = "BLOCK_ALL_FEES"
    ADVISORY = "LOG_AND_PROCEED"

class SRENConfig(BaseModel):
    mode: EnforcementMode = EnforcementMode.STRICT
    allow_value_added_services: bool = False

STATUTORY_MAX_EGRESS_FEE: Final[Decimal] = Decimal("0.00")

class DataSovereigntyViolation(Exception):
    def __init__(self, provider: str, cost: Decimal, context: str):
        self.message = (
            f"[VIOLATION] Provider {provider} attempts to charge {cost} EUR/GB. "
            f"Limit is {STATUTORY_MAX_EGRESS_FEE} EUR per {LegalReference.ARRETE_EGRESS.value}."
        )
        super().__init__(self.message)
