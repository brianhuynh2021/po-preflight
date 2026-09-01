from __future__ import annotations

from abc import ABC, abstractmethod
from preflight.erp.schemas import ERPSyncPayload, ERPSyncResponse


class BaseERPAdapter(ABC):
    """Abstract interface for ERP Sales Order synchronization."""

    @abstractmethod
    def sync_order(self, payload: ERPSyncPayload) -> ERPSyncResponse:
        """Synchronize an approved purchase order to upstream ERP."""
        raise NotImplementedError
