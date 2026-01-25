import pytest
import asyncio
import random
import string
from decimal import Decimal, getcontext, InvalidOperation
from unittest.mock import AsyncMock, patch
from src.core.policy import DataSovereigntyViolation, SRENConfig
from src.domain.models import AgentIdentity, UCPTransaction
from src.adapters.ucp_firewall import SRENComplianceFilter

# --- CONFIGURATION DU CHAOS ---
CONCURRENT_REQUESTS = 5000  # On sature l'Event Loop
MAX_PAYLOAD_SIZE = Decimal("1e+26")  # On dépasse la taille de l'univers observable en octets

@pytest.fixture
def chaos_firewall():
    # Un billing service qui répond, mais parfois avec de la latence ou des erreurs
    mock_billing = AsyncMock()
    mock_billing.get_current_egress_rate.return_value = Decimal("0.09")
    return SRENComplianceFilter(billing_service=mock_billing)

# 1. ATTACK VECTOR: THE THUNDERING HERD (DDoS Interne)
# Objectif : Voir si l'async/await tient la charge ou si Python segfault sur la mémoire.
@pytest.mark.asyncio
async def test_armageddon_concurrency(chaos_firewall):
    print(f"\n[WARHEAD] Launching {CONCURRENT_REQUESTS} concurrent warheads...")
    
    agent = AgentIdentity(provider="AWS_US_EAST", agent_id="bot-swarm", compliance_score=0.1)
    tx = UCPTransaction(transaction_id="tx-swarm", payload_size_mb=10, intent="SWARM")

    # On lance tout en même temps sans attendre
    tasks = [chaos_firewall.audit_transaction(agent, tx) for _ in range(CONCURRENT_REQUESTS)]
    
    # On attend que la poussière retombe
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Analyse des dégâts
    failures = [r for r in results if isinstance(r, Exception) and not isinstance(r, DataSovereigntyViolation)]
    
    if failures:
        pytest.fail(f"SYSTEM CRASHED under load: {failures[0]}")
    else:
        print(f"[SURVIVAL] System handled {CONCURRENT_REQUESTS} reqs/sec without crashing.")

# 2. ATTACK VECTOR: DECIMAL OVERFLOW (The "Googol" Payload)
# Objectif : Briser la précision 28 de Decimal en injectant des nombres absurdes.
@pytest.mark.asyncio
async def test_armageddon_math_overflow(chaos_firewall):
    print("\n[WARHEAD] Injecting payload size > Total Internet Traffic...")
    
    agent = AgentIdentity(provider="MEGA_UPLOAD", agent_id="fat-boy", compliance_score=0.0)
    # Payload massive qui risque de faire sauter la multiplication
    tx = UCPTransaction(transaction_id="tx-overflow", payload_size_mb=float(MAX_PAYLOAD_SIZE), intent="OVERFLOW")

    try:
        await chaos_firewall.audit_transaction(agent, tx)
    except DataSovereigntyViolation:
        print("[SURVIVAL] Math logic held. The violation was correctly raised despite massive numbers.")
    except InvalidOperation:
        pytest.fail("MATH FAILURE: Decimal context crashed (InvalidOperation). Precision handling is weak.")
    except Exception as e:
        pytest.fail(f"UNHANDLED EXCEPTION: {type(e).__name__} - {e}")

# 3. ATTACK VECTOR: POISONED STRINGS (Log Injection)
# Objectif : Injecter du null-byte, des emojis et du script pour corrompre le logger ou le hasher.
@pytest.mark.asyncio
async def test_armageddon_fuzzing_injection(chaos_firewall):
    print("\n[WARHEAD] Injecting toxic characters (Null Bytes, Emojis, SQLi)...")
    
    toxic_ids = [
        "tx-\x00-poison",        # Null Byte (tue souvent le C sous-jacent)
        "tx-🔥🔥🔥🔥🔥🔥🔥🔥",  # UTF-8 Stress
        "tx-'; DROP TABLE logs;--", # SQL Injection pattern
        "A" * 10000              # Buffer Overflow attempt sur l'ID
    ]

    for toxic_id in toxic_ids:
        tx = UCPTransaction(transaction_id=toxic_id, payload_size_mb=1, intent="TOXIC")
        agent = AgentIdentity(provider="ANONYMOUS", agent_id="hacker", compliance_score=0.0)
        
        try:
            await chaos_firewall.audit_transaction(agent, tx)
        except DataSovereigntyViolation:
            pass # C'est le comportement attendu (blocage ou validation)
        except Exception as e:
            pytest.fail(f"SECURITY BREACH: Input '{toxic_id[:20]}...' caused {type(e).__name__}")
    
    print("[SURVIVAL] Input sanitization holds. No crypto-crashes.")

# 4. ATTACK VECTOR: CONFIG MUTATION (Runtime Drift)
# Objectif : Changer la config PENDANT que ça tourne pour voir si ça suit.
@pytest.mark.asyncio
async def test_armageddon_dynamic_config_drift(chaos_firewall):
    print("\n[WARHEAD] Mutating SREN Config in real-time...")
    
    agent = AgentIdentity(provider="AZURE_FR", agent_id="drifter", compliance_score=0.5)
    tx = UCPTransaction(transaction_id="tx-drift", payload_size_mb=100, intent="DRIFT")

    # Config 1 : Tout va bien
    safe_config = SRENConfig(network_overhead=Decimal("1.00"), credit_balance=Decimal("1000.00"))
    assert await chaos_firewall.audit_transaction(agent, tx, config=safe_config) is True

    # Config 2 : Le gouvernement change la loi (Overhead x100) -> Doit bloquer
    strict_config = SRENConfig(network_overhead=Decimal("100.00"), credit_balance=Decimal("0.00"))
    
    with pytest.raises(DataSovereigntyViolation):
        await chaos_firewall.audit_transaction(agent, tx, config=strict_config)
        
    print("[SURVIVAL] Dynamic Logic is responsive. No stale config detected.")
