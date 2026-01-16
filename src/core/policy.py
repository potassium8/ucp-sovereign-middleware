"""
CORE POLICY ENGINE
Authority: Arrêté du 17 novembre 2025 (NOR: ECOI2530768A)
Compliance Target: Article 27, Loi n° 2024-449.
"""

from enum import Enum
from decimal import Decimal
from typing import Final

class LegalReference(Enum):
    SREN_ART_27 = "LOI_2024_449_ART_27"
    ARRETE_EGRESS = "NOR_ECOI2530768A"  # Arrêté du 17/11/2025
    GDPR_PORTABILITY = "RGPD_ART_20"

# Conformément au JORF n°0281 du 30/11/2025
# Montant maximal autorisé pour les frais de transfert
STATUTORY_MAX_EGRESS_FEE: Final[Decimal] = Decimal("0.00")

class DataSovereigntyViolation(Exception):
    """
    Raised when an infrastructure component violates French Digital Sovereignty Laws.
    Target: Blocking non-compliant UCP streams.
    """
    def __init__(self, provider: str, cost: Decimal, context: str):
        self.message = (
            f"[VIOLATION] Provider {provider} attempts to charge {cost} EUR/GB. "
            f"Limit is {STATUTORY_MAX_EGRESS_FEE} EUR per {LegalReference.ARRETE_EGRESS.value}. "
            f"Context: {context}"
        )
        super().__init__(self.message)
