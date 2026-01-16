from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class AgentIdentity(BaseModel):
    """
    Identity card of the AI Agent requesting access.
    """
    provider: Literal["GOOGLE_UCP", "OPENAI_OAI", "INTERNAL_RAG", "UNKNOWN"]
    agent_id: str
    compliance_score: float = Field(..., ge=0.0, le=1.0, description="Trust score based on previous audits")

class UCPTransaction(BaseModel):
    """
    Represents a transaction intent within the Universal Commerce Protocol.
    """
    transaction_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    payload_size_mb: float = Field(..., gt=0, description="Size of the catalog segment requested")
    intent: str
    
    # The critical field for SREN: Does this data leave the sovereign perimeter?
    requires_data_egress: bool = True
