from __future__ import annotations

import time
from preflight.erp.adapters.base import BaseERPAdapter
from preflight.erp.schemas import ERPAdapterType, ERPSyncPayload, ERPSyncResponse


class MockSAPAdapter(BaseERPAdapter):
    """Simulates SAP S/4HANA BAPI / OData Sales Order Creation."""

    def __init__(self, endpoint_url: str = "https://sap.enterprise.internal/odata/v2/SalesOrder"):
        self.endpoint_url = endpoint_url

    def sync_order(self, payload: ERPSyncPayload) -> ERPSyncResponse:
        # Generate SAP Document Number (10 digits)
        clean_code = "".join(filter(str.isdigit, payload.po_number)) or "1001"
        sap_doc_num = f"SAP-SO-{clean_code.zfill(6)}"

        return ERPSyncResponse(
            success=True,
            transaction_id=sap_doc_num,
            adapter_type=ERPAdapterType.MOCK_SAP,
            idempotency_key=payload.idempotency_key,
            timestamp=time.time(),
            error_message=None,
        )
