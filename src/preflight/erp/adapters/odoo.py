from __future__ import annotations

import time
from preflight.erp.adapters.base import BaseERPAdapter
from preflight.erp.schemas import ERPAdapterType, ERPSyncPayload, ERPSyncResponse


class MockOdooAdapter(BaseERPAdapter):
    """Simulates Odoo 17 JSON-RPC sale.order Creation."""

    def __init__(self, endpoint_url: str = "https://odoo.enterprise.internal/jsonrpc"):
        self.endpoint_url = endpoint_url

    def sync_order(self, payload: ERPSyncPayload) -> ERPSyncResponse:
        # Generate Odoo Reference (SO/2026/XXXX)
        clean_code = "".join(filter(str.isdigit, payload.po_number)) or "0001"
        odoo_ref = f"SO/2026/{clean_code.zfill(4)}"

        return ERPSyncResponse(
            success=True,
            transaction_id=odoo_ref,
            adapter_type=ERPAdapterType.MOCK_ODOO,
            idempotency_key=payload.idempotency_key,
            timestamp=time.time(),
            error_message=None,
        )
