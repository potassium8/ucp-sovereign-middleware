import pytest
from decimal import Decimal
from src.adapters.ucp_firewall import SRENComplianceFilter
from src.adapters.cloud.aws_billing import AWSBillingAdapter
from src.core.policy import DataSovereigntyViolation
from src.domain.models import AgentIdentity, UCPTransaction

@pytest.mark.asyncio
async def test_it_blocks_google_ucp_if_egress_fees_exist():
    billing_service = AWSBillingAdapter()
    firewall = SRENComplianceFilter(billing_service=billing_service)

    google_agent = AgentIdentity(
        provider="GOOGLE_UCP", 
        agent_id="agent-007", 
        compliance_score=0.5
    )
    
    tx = UCPTransaction(
        transaction_id="tx-123", 
        payload_size_mb=5000, 
        intent="CATALOG_INGESTION"
    )

    with pytest.raises(DataSovereigntyViolation) as excinfo:
        await firewall.audit_transaction(google_agent, tx)
    
    assert "NOR_ECOI2530768A" in str(excinfo.value)
    print(f"\n[SUCCESS] Law enforcement verified: {excinfo.value}")
