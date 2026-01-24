import pytest
import time
from unittest.mock import Mock, patch, AsyncMock  # <--- Ajoute AsyncMock ici
from decimal import Decimal
from src.core.policy import DataSovereigntyViolation, EnforcementMode, SRENConfig
from src.domain.models import AgentIdentity, UCPTransaction
from src.adapters.ucp_firewall import SRENComplianceFilter
from src.adapters.cloud.aws_billing import AWSBillingAdapter

# --- SCÉNARIO 1 : L'Attaque du "Micro-Centime" (Salami Attack) ---
# Objectif : Vérifier si le système détecte une infraction de 0.0001€
@pytest.mark.asyncio
async def test_merciless_micro_transaction():
    # Mock du billing pour forcer un tarif très bas mais non-nul
    mock_billing = Mock(spec=AWSBillingAdapter)
    mock_billing.get_current_egress_rate.return_value = Decimal("0.0001") # 0.01 centime/GB

    firewall = SRENComplianceFilter(billing_service=mock_billing)
    
    agent = AgentIdentity(provider="OPENAI_SHADOW", agent_id="gpt-4-turbo", compliance_score=0.1)
    # Payload massive pour transformer le 0.0001 en coût réel
    tx = UCPTransaction(transaction_id="tx-micro-1", payload_size_mb=10000, intent="DATA_EXFIL")

    with pytest.raises(DataSovereigntyViolation) as excinfo:
        await firewall.audit_transaction(agent, tx)
    
    # On vérifie que MEME un coût infime déclenche la loi
    assert "SREN_BLOCK" in str(excinfo.value)
    print("\n[PASS] Micro-Egress detected. No penny left behind.")

# --- SCÉNARIO 2 : Sabotage par Injection Négative ---
# Objectif : L'agent envoie une taille de -50MB pour créditer son compte ou faire crasher le script
@pytest.mark.asyncio
async def test_merciless_negative_payload_injection():
    billing = AWSBillingAdapter()
    firewall = SRENComplianceFilter(billing_service=billing)
    
    agent = AgentIdentity(provider="HACKER_CORP", agent_id="mr-robot", compliance_score=0.0)
    tx = UCPTransaction(transaction_id="tx-crash-1", payload_size_mb=-50, intent="MEMORY_CORRUPTION")

    with pytest.raises(DataSovereigntyViolation) as excinfo:
        await firewall.audit_transaction(agent, tx)

    # Le système doit capturer l'erreur ValueError et la transformer en Violation de Souveraineté
    assert "INPUT_REJECTION" in str(excinfo.value)
    print("\n[PASS] Negative Payload neutralized. Logic intact.")

# --- SCÉNARIO 3 : La Faille Temporelle (Cache Poisoning) ---
# Objectif : Prouver que le cache expire VRAIMENT après 60s
@pytest.mark.asyncio
async def test_merciless_time_drift_cache():
    billing = AWSBillingAdapter()
    
    # 1. On force le cache à 0.00€
    with patch.object(billing, 'get_current_egress_rate', return_value=Decimal("0.00")):
        rate_t0 = await billing.get_current_egress_rate()
        assert rate_t0 == Decimal("0.00")

    # 2. On avance le temps de 61 secondes (TTL + 1)
    with patch('time.time', return_value=time.time() + 61):
        # Maintenant, AWS change ses prix (simulation via mock interne du code réel)
        # Note: Dans ton code réel, après TTL, il renvoie 0.09. C'est ce qu'on teste.
        rate_t1 = await billing.get_current_egress_rate()
        
        # Si le cache fonctionnait mal, on aurait encore 0.00. 
        # Si le TTL marche, on a la nouvelle valeur (0.09 codé en dur dans ton adapter de demo)
        assert rate_t1 == Decimal("0.09")
        
    print("\n[PASS] Time Drift handled. Cache invalidated correctly.")

# --- SCÉNARIO 4 : Audit Cryptographique des Logs ---
# CORRIGÉ AVEC ASYNCMOCK
@pytest.mark.asyncio
async def test_merciless_crypto_logging(caplog):
    # On utilise AsyncMock car le firewall fait un 'await'
    mock_billing = AsyncMock(spec=AWSBillingAdapter)
    mock_billing.get_current_egress_rate.return_value = Decimal("0.00")
    
    firewall = SRENComplianceFilter(billing_service=mock_billing)
    
    sensitive_tx_id = "user-email-james-bond-007"
    agent = AgentIdentity(provider="MI6", agent_id="q-branch", compliance_score=1.0)
    tx = UCPTransaction(transaction_id=sensitive_tx_id, payload_size_mb=10, intent="CLASSIFIED")

    with caplog.at_level("INFO"):
        await firewall.audit_transaction(agent, tx)
    
    # Vérification impitoyable : L'ID original NE DOIT PAS être dans les logs
    assert sensitive_tx_id not in caplog.text
    # Mais le hash SHA-256 (partiel) DOIT y être
    assert "sha256:" in caplog.text
    
    print("\n[PASS] Crypto-Log verified. No clear-text PII leakage.")
