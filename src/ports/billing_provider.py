from abc import ABC, abstractmethod
from decimal import Decimal

class BillingProvider(ABC):
    """
    Interface for Real-time Cloud Billing Ingestion.
    Ensures the middleware remains Cloud-Agnostic.
    """
    @abstractmethod
    async def get_current_egress_rate(self) -> Decimal:
        """
        Fetch real-time egress rate from provider API.
        Implementation should target AWS Cost Explorer, GCP Billing, or Scaleway API.
        """
        pass
