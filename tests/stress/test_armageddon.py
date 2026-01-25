import pytest
import asyncio
from decimal import Decimal, InvalidOperation
from unittest.mock import AsyncMock
from src.core.policy import DataSovereigntyViolation, SRENConfig, create_secure_config
from src.domain.models import AgentIdentity, UCPTransaction
from src.adapters.ucp_firewall import SRENComplianceFilter

CONCURRENT_REQUESTS = 5000 
MAX_PAYLOAD_SIZE = Decimal("1e+26") 

@pytest.fixture
def stress_firewall():
    mock_billing = AsyncMock()
    mock_billing.get_current_egress_rate.return_value = Decimal("0.09")
    return SRENComplianceFilter(billing_service=mock_billing)

@pytest.mark.asyncio
async def test_high_concurrency_load(stress_firewall):
    agent = AgentIdentity(provider="AWS_US_EAST", agent_id="bot-swarm", compliance_score=0.1)
    tx = UCPTransaction(transaction_id="tx-swarm", payload_size_mb=10, intent="SWARM")

    tasks = [stress_firewall.audit_transaction(agent, tx) for _ in range(CONCURRENT_REQUESTS)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    failures = [r for r in results if isinstance(r, Exception) and not isinstance(r, DataSovereigntyViolation)]
    
    if failures:
        pytest.fail(f"System instability detected under load: {failures[0]}")

@pytest.mark.asyncio
async def test_decimal_precision_overflow(stress_firewall):
    agent = AgentIdentity(provider="MEGA_UPLOAD", agent_id="fat-boy", compliance_score=0.0)
    tx = UCPTransaction(transaction_id="tx-overflow", payload_size_mb=float(MAX_PAYLOAD_SIZE), intent="OVERFLOW")

    try:
        await stress_firewall.audit_transaction(agent, tx)
    except DataSovereigntyViolation:
        pass 
    except InvalidOperation:
        pytest.fail("Decimal context crash: Precision handling insufficient.")
    except Exception as e:
        pytest.fail(f"Unhandled exception during overflow test: {type(e).__name__}")

@pytest.mark.asyncio
async def test_integrity_tampering(stress_firewall):
    agent = AgentIdentity(provider="NSA", agent_id="spy", compliance_score=0.0)
    tx = UCPTransaction(transaction_id="tx-spy", payload_size_mb=10, intent="SPY")

    secure_config = create_secure_config(overhead=Decimal("1.00"))
    
    object.__setattr__(secure_config, 'network_overhead', Decimal("0.00"))

    with pytest.raises(DataSovereigntyViolation) as excinfo:
        await stress_firewall.audit_transaction(agent, tx, config=secure_config)
    
    assert "INTEGRITY_COMPROMISE" in str(excinfo.value)

@pytest.mark.asyncio
async def test_runtime_config_mutation(stress_firewall):
    agent = AgentIdentity(provider="AZURE_FR", agent_id="drifter", compliance_score=0.5)
    tx = UCPTransaction(transaction_id="tx-drift", payload_size_mb=100, intent="DRIFT")

    safe_config = create_secure_config(overhead=Decimal("1.00"), credits=Decimal("1000.00"))
    assert await stress_firewall.audit_transaction(agent, tx, config=safe_config) is True

    strict_config = create_secure_config(overhead=Decimal("100.00"), credits=Decimal("0.00"))
    with pytest.raises(DataSovereigntyViolation):
        await stress_firewall.audit_transaction(agent, tx, config=strict_config)
