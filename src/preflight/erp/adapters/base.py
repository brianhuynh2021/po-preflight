from __future__ import annotations

from abc import ABC, abstractmethod
from preflight.erp.schemas import ERPAdapterType, ERPSyncPayload, ERPSyncResponse
from preflight.models import InventorySnapshot


class BaseERPAdapter(ABC):
    """Abstract interface for ERP Sales Order synchronization and inventory fetching."""

    adapter_type: ERPAdapterType = ERPAdapterType.MOCK_SAP

    @abstractmethod
    def sync_order(self, payload: ERPSyncPayload) -> ERPSyncResponse:
        """Synchronize an approved purchase order to upstream ERP."""
        raise NotImplementedError

    @abstractmethod
    def fetch_inventory(self, skus: list[str] | None = None) -> list[InventorySnapshot]:
        """Fetch real-time or snapshot inventory levels from ERP."""
        raise NotImplementedError
