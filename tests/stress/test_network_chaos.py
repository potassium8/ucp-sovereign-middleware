import pytest
import asyncio
from unittest.mock import AsyncMock
from decimal import Decimal
from src.core.policy import DataSovereigntyViolation
from src.domain.models import AgentIdentity, UCPTransaction
from src.adapters.ucp_firewall import SRENComplianceFilter

@pytest.mark.asyncio
async def test_network_timeout_resilience():
    """Simulates a Gateway Timeout (Blackhole) to verify Fail-Safe mode."""
    mock_billing = AsyncMock()
    mock_billing.get_current_egress_rate.side_effect = asyncio.TimeoutError("CONNECTION_TIMED_OUT")
    
    firewall = SRENComplianceFilter(billing_service=mock_billing)
    agent = AgentIdentity(provider="AWS", agent_id="chaos-bot", compliance_score=0.5)
    tx = UCPTransaction(transaction_id="tx-timeout", payload_size_mb=10, intent="TEST")

    with pytest.raises(DataSovereigntyViolation) as excinfo:
        await firewall.audit_transaction(agent, tx)
    
    assert "FAIL_SAFE_SHUTDOWN" in str(excinfo.value)

@pytest.mark.asyncio
async def test_connection_reset_handling():
    """Simulates a Connection Reset (RST) from the upstream provider."""
    mock_billing = AsyncMock()
    mock_billing.get_current_egress_rate.side_effect = ConnectionResetError("PEER_RESET_CONNECTION")
    
    firewall = SRENComplianceFilter(billing_service=mock_billing)
    agent = AgentIdentity(provider="AZURE", agent_id="chaos-bot", compliance_score=0.5)
    tx = UCPTransaction(transaction_id="tx-reset", payload_size_mb=10, intent="TEST")

    with pytest.raises(DataSovereigntyViolation) as excinfo:
        await firewall.audit_transaction(agent, tx)

    assert "FAIL_SAFE_SHUTDOWN" in str(excinfo.value)

@pytest.mark.asyncio
async def test_high_latency_tolerance():
    """Verifies that high latency (500ms) does not block the Event Loop."""
    async def delayed_response():
        await asyncio.sleep(0.5) 
        # Return 0.00 to pass financial check after the delay
        return Decimal("0.00") 

    mock_billing = AsyncMock()
    mock_billing.get_current_egress_rate.side_effect = delayed_response
    
    firewall = SRENComplianceFilter(billing_service=mock_billing)
    agent = AgentIdentity(provider="GCP", agent_id="slow-bot", compliance_score=0.5)
    tx = UCPTransaction(transaction_id="tx-slow", payload_size_mb=10, intent="TEST")

    result = await firewall.audit_transaction(agent, tx)
    assert result is True
