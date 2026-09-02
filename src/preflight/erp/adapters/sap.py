import time
from datetime import datetime, timezone
from decimal import Decimal
from preflight.erp.adapters.base import BaseERPAdapter
from preflight.erp.schemas import ERPAdapterType, ERPSyncPayload, ERPSyncResponse
from preflight.models import InventorySnapshot


class MockSAPAdapter(BaseERPAdapter):
    """Simulates SAP S/4HANA BAPI / OData Sales Order Creation and Stock Inquiry."""

    adapter_type = ERPAdapterType.MOCK_SAP

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
            mode="mock",
            timestamp=time.time(),
            error_message=None,
        )

    def fetch_inventory(self, skus: list[str] | None = None) -> list[InventorySnapshot]:
        now_iso = datetime.now(timezone.utc).isoformat()
        default_stock_map = {
            "LAPTOP-A14": (Decimal("50"), Decimal("0")),
            "MONITOR-27": (Decimal("30"), Decimal("0")),
            "CAB-CAT6-3M": (Decimal("100"), Decimal("0")),
            "HEADSET-PRO": (Decimal("0"), Decimal("0")),
            "KEYBOARD-M1": (Decimal("25"), Decimal("0")),
            "MOUSE-W2": (Decimal("40"), Decimal("0")),
        }
        target_skus = skus if skus is not None else list(default_stock_map.keys())
        snapshots = []
        for sku in target_skus:
            on_hand, reserved = default_stock_map.get(sku, (Decimal("50"), Decimal("0")))
            snapshots.append(
                InventorySnapshot(
                    sku=sku,
                    warehouse="SAP-PLANT-1000",
                    on_hand=on_hand,
                    reserved=reserved,
                    as_of=now_iso,
                    source="mock_sap",
                )
            )
        return snapshots

