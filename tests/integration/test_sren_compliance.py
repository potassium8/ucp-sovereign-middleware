import pytest
from decimal import Decimal
from src.adapters.ucp_firewall import SRENComplianceFilter
from src.core.policy import DataSovereigntyViolation
from src.domain.models import AgentIdentity, UCPTransaction

@pytest.mark.asyncio
async def test_it_blocks_google_ucp_if_egress_fees_exist():
    """
    Scenario: A Google UCP Agent tries to ingest a catalog.
    Infrastructure: Legacy Cloud Provider charging 0.09 EUR/GB.
    Expected Result: BLOCKED by SREN Law (Article 27).
    """
    # GIVEN: A standard AWS setup charging egress
    aws_standard_rate = Decimal("0.09") 
    firewall = SRENComplianceFilter(cloud_provider_rate_per_gb=aws_standard_rate)

    # AND: A Google Agent requesting heavy data
    google_agent = AgentIdentity(
        provider="GOOGLE_UCP", 
        agent_id="agent-007", 
        compliance_score=0.5
    )
    tx = UCPTransaction(
        transaction_id="tx-123", 
        payload_size_mb=5000, # 5GB
        intent="CATALOG_INGESTION"
    )

    # WHEN / THEN: The SREN Law must trigger an exception
    with pytest.raises(DataSovereigntyViolation) as excinfo:
        await firewall.audit_transaction(google_agent, tx)
    
    # Verify the Legal Reference is cited in the error
    assert "NOR_ECOI2530768A" in str(excinfo.value)
    print("\n[SUCCESS] The middleware successfully enforced French Law against the Agent.")
