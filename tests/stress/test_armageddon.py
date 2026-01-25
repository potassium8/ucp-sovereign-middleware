import pytest
import asyncio
from decimal import Decimal, InvalidOperation
from unittest.mock import AsyncMock
from src.core.policy import DataSovereigntyViolation, SRENConfig
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
    """Validates system stability under high concurrent load (AsyncIO Event Loop)."""
    agent = AgentIdentity(provider="AWS_US_EAST", agent_id="bot-swarm", compliance_score=0.1)
    tx = UCPTransaction(transaction_id="tx-swarm", payload_size_mb=10, intent="SWARM")

    tasks = [stress_firewall.audit_transaction(agent, tx) for _ in range(CONCURRENT_REQUESTS)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    failures = [r for r in results if isinstance(r, Exception) and not isinstance(r, DataSovereigntyViolation)]
    
    if failures:
        pytest.fail(f"System instability detected under load: {failures[0]}")

@pytest.mark.asyncio
async def test_decimal_precision_overflow(stress_firewall):
    """Checks Decimal handling against massive numbers to prevent rounding errors."""
    agent = AgentIdentity(provider="MEGA_UPLOAD", agent_id="fat-boy", compliance_score=0.0)
    tx = UCPTransaction(transaction_id="tx-overflow", payload_size_mb=float(MAX_PAYLOAD_SIZE), intent="OVERFLOW")

    try:
        await stress_firewall.audit_transaction(agent, tx)
    except DataSovereigntyViolation:
        pass # Expected behavior
    except InvalidOperation:
        pytest.fail("Decimal context crash: Precision handling insufficient.")
    except Exception as e:
        pytest.fail(f"Unhandled exception during overflow test: {type(e).__name__}")

@pytest.mark.asyncio
async def test_input_fuzzing_and_injection(stress_firewall):
    """Fuzzing test: Injects null bytes, emojis, and SQL-like strings."""
    toxic_ids = [
        "tx-\x00-poison",        
        "tx-🔥🔥🔥🔥🔥🔥🔥🔥",  
        "tx-'; DROP TABLE logs;--", 
        "A" * 10000              
    ]

    for toxic_id in toxic_ids:
        tx = UCPTransaction(transaction_id=toxic_id, payload_size_mb=1, intent="TOXIC")
        agent = AgentIdentity(provider="ANONYMOUS", agent_id="hacker", compliance_score=0.0)
        
        try:
            await stress_firewall.audit_transaction(agent, tx)
        except DataSovereigntyViolation:
            pass 
        except Exception as e:
            pytest.fail(f"Sanitization failure for input '{toxic_id[:20]}...': {type(e).__name__}")

@pytest.mark.asyncio
async def test_runtime_config_mutation(stress_firewall):
    """Ensures SRENConfig changes are applied immediately at runtime."""
    agent = AgentIdentity(provider="AZURE_FR", agent_id="drifter", compliance_score=0.5)
    tx = UCPTransaction(transaction_id="tx-drift", payload_size_mb=100, intent="DRIFT")

    # Config 1: Permissive
    safe_config = SRENConfig(network_overhead=Decimal("1.00"), credit_balance=Decimal("1000.00"))
    assert await stress_firewall.audit_transaction(agent, tx, config=safe_config) is True

    # Config 2: Strict
    strict_config = SRENConfig(network_overhead=Decimal("100.00"), credit_balance=Decimal("0.00"))
    with pytest.raises(DataSovereigntyViolation):
        await stress_firewall.audit_transaction(agent, tx, config=strict_config)
