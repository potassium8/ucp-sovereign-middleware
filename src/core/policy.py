import os
import hmac
import hashlib
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

INTERNAL_HMAC_KEY = os.environ.get("SREN_SIGNING_KEY", "DEFAULT_FALLBACK_NOT_FOR_PROD").encode()

STATUTORY_MAX_EGRESS_FEE = Decimal("0.00")
UCP_PROTOCOL_OVERHEAD = Decimal("1.02")

class EnforcementMode(Enum):
    STRICT = "strict"
    AUDIT = "audit"

@dataclass(frozen=True)
class DataSovereigntyViolation(Exception):
    provider: str
    cost: Decimal
    reason: str

    def __str__(self):
        return f"[VIOLATION] {self.provider} attempts to charge {self.cost} EUR/GB. Reason: {self.reason}. Ref: NOR:ECOI2530768A"

@dataclass(frozen=True)
class SRENConfig:
    mode: EnforcementMode = EnforcementMode.STRICT
    allow_value_added_services: bool = False
    hash_algorithm: str = "sha256"
    credit_balance: Decimal = Decimal("0.00")
    network_overhead: Decimal = Decimal("1.02")
    integrity_signature: str = ""

    def verify_integrity(self) -> bool:
        payload = f"{self.mode.value}{self.allow_value_added_services}{self.hash_algorithm}{self.credit_balance}{self.network_overhead}"
        expected_sig = hmac.new(INTERNAL_HMAC_KEY, payload.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.integrity_signature, expected_sig)

def create_secure_config(
    mode: EnforcementMode = EnforcementMode.STRICT, 
    allow_vas: bool = False,
    overhead: Decimal = Decimal("1.02"), 
    credits: Decimal = Decimal("0.00"),
    algo: str = "sha256"
) -> SRENConfig:
    payload = f"{mode.value}{allow_vas}{algo}{credits}{overhead}"
    signature = hmac.new(INTERNAL_HMAC_KEY, payload.encode(), hashlib.sha256).hexdigest()
    
    return SRENConfig(
        mode=mode,
        allow_value_added_services=allow_vas,
        hash_algorithm=algo,
        credit_balance=credits,
        network_overhead=overhead,
        integrity_signature=signature
    )
