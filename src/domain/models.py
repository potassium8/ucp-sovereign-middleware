from decimal import Decimal
from dataclasses import dataclass

@dataclass(frozen=True)
class AgentIdentity:
    provider: str
    agent_id: str
    compliance_score: float
    region: str = "eu-west-1"

@dataclass(frozen=True)
class UCPTransaction:
    transaction_id: str
    payload_size_mb: Decimal
    intent: str
