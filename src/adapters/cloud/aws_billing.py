import time
from decimal import Decimal
from src.ports.billing_provider import BillingProvider

class AWSBillingAdapter(BillingProvider):
    def __init__(self):
        self._cache_rate = Decimal("0.00")
        self._last_fetch_time = 0
        self._cache_ttl = 60  # Cache valide 60 secondes

    async def get_current_egress_rate(self) -> Decimal:
        current_time = time.time()
        
        if current_time - self._last_fetch_time < self._cache_ttl:
            return self._cache_rate

        # Simulation appel API (Boto3)
        # En prod: response = client.get_cost_forecast(...)
        real_time_rate = Decimal("0.09") 
        
        # Mise à jour du cache
        self._cache_rate = real_time_rate
        self._last_fetch_time = current_time
        
        return self._cache_rate
