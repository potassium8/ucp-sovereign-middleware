import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from src.core.policy import DataSovereigntyViolation, EnforcementMode, create_secure_config
from src.domain.models import AgentIdentity, UCPTransaction
from src.adapters.ucp_firewall import SRENComplianceFilter
from src.adapters.cloud.aws_billing import AWSBillingAdapter

@pytest.mark.asyncio
async def test_micro_transaction_compliance():
    mock_billing = AsyncMock(spec=AWSBillingAdapter)
    mock_billing.get_current_egress_rate.return_value = Decimal("0.0001") 

    firewall = SRENComplianceFilter(billing_service=mock_billing)
    
    agent = AgentIdentity(provider="OPENAI_SHADOW", agent_id="gpt-4-turbo", compliance_score=0.1)
    tx = UCPTransaction(transaction_id="tx-micro-1", payload_size_mb=10000, intent="DATA_EXFIL")

    with pytest.raises(DataSovereigntyViolation) as excinfo:
        await firewall.audit_transaction(agent, tx)
    
    assert "SREN_BLOCK" in str(excinfo.value)

@pytest.mark.asyncio
async def test_negative_payload_injection():
    billing = AsyncMock(spec=AWSBillingAdapter)
    firewall = SRENComplianceFilter(billing_service=billing)
    
    agent = AgentIdentity(provider="HACKER_CORP", agent_id="mr-robot", compliance_score=0.0)
    tx = UCPTransaction(transaction_id="tx-crash-1", payload_size_mb=-50, intent="MEMORY_CORRUPTION")

    with pytest.raises(DataSovereigntyViolation) as excinfo:
        await firewall.audit_transaction(agent, tx)

    assert "INPUT_REJECTION" in str(excinfo.value)

@pytest.mark.asyncio
async def test_time_drift_cache_invalidation():
    billing = AWSBillingAdapter()
    
    with patch.object(billing, 'get_current_egress_rate', return_value=Decimal("0.00")):
        rate_t0 = await billing.get_current_egress_rate()
        assert rate_t0 == Decimal("0.00")

    with patch('time.time', return_value=time.time() + 61):
        rate_t1 = await billing.get_current_egress_rate()
        assert rate_t1 == Decimal("0.09")

@pytest.mark.asyncio
async def test_pii_logging_compliance(caplog):
    mock_billing = AsyncMock(spec=AWSBillingAdapter)
    mock_billing.get_current_egress_rate.return_value = Decimal("0.00")
    
    firewall = SRENComplianceFilter(billing_service=mock_billing)
    
    sensitive_tx_id = "user-email-james-bond-007"
    agent = AgentIdentity(provider="MI6", agent_id="q-branch", compliance_score=1.0)
    tx = UCPTransaction(transaction_id=sensitive_tx_id, payload_size_mb=10, intent="CLASSIFIED")

    with caplog.at_level("INFO"):
        await firewall.audit_transaction(agent, tx)
    
    assert sensitive_tx_id not in caplog.text
    assert "sha256:" in caplog.text or "sha3" in caplog.text
