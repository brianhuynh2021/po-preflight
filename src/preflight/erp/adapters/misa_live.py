from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

from preflight.erp.adapters.base import BaseERPAdapter
from preflight.erp.exceptions import ERPConfigurationError
from preflight.erp.schemas import ERPAdapterType, ERPSyncPayload, ERPSyncResponse

logger = logging.getLogger("PreflightMisaAmisLiveAdapter")


class MisaAmisLiveAdapter(BaseERPAdapter):
    """Production MISA AMIS Open API Connector for Vietnamese SME Enterprise ERP.
    Publishes sales orders into MISA sa_order and sa_order_detail vouchers.
    """

    adapter_type = ERPAdapterType.MISA_AMIS_LIVE

    def __init__(
        self,
        base_url: str | None = None,
        app_id: str | None = None,
        access_token: str | None = None,
        dry_run: bool = False,
    ):
        self.base_url = base_url or os.getenv("MISA_API_URL", "https://api.misa.vn/amis/v1")
        self.app_id = app_id or os.getenv("MISA_APP_ID", "misa_preflight_app")
        self.access_token = access_token or os.getenv("MISA_ACCESS_TOKEN", "")
        self.dry_run = dry_run or os.getenv("MISA_DRY_RUN", "true").lower() == "true"

    def sync_order(self, payload: ERPSyncPayload) -> ERPSyncResponse:
        """Create MISA AMIS sales order voucher."""
        if self.dry_run or not self.access_token:
            if os.getenv("PREFLIGHT_ENV") == "production":
                raise ERPConfigurationError("MISA credentials missing in production environment.")

            logger.warning(f"MISA live adapter running in dry_run mode for PO '{payload.po_number}'")
            clean_digits = "".join(filter(str.isdigit, payload.po_number)) or "20261001"
            misa_voucher_no = f"DRYRUN-DH-{clean_digits}"
            return ERPSyncResponse(
                success=True,
                transaction_id=misa_voucher_no,
                adapter_type=ERPAdapterType.MISA_AMIS_LIVE,
                idempotency_key=payload.idempotency_key,
                mode="dry_run",
                timestamp=time.time(),
                error_message=None,
            )

        try:
            # Build MISA AMIS Standard Voucher Structure
            detail_lines = []
            for it in payload.items:
                detail_lines.append(
                    {
                        "inventory_item_code": it.get("sku"),
                        "description": it.get("description", it.get("sku")),
                        "unit_name": it.get("uom", "Cái"),
                        "quantity": float(it.get("quantity", 1)),
                        "unit_price": float(it.get("unit_price", 0)),
                        "amount": float(it.get("quantity", 1)) * float(it.get("unit_price", 0)),
                    }
                )

            misa_payload = {
                "voucher_type": "SAOrder",
                "account_object_name": payload.customer,
                "order_number": payload.po_number,
                "total_amount": float(payload.total_amount),
                "currency_id": payload.currency,
                "sa_order_detail": detail_lines,
            }

            req_data = json.dumps(misa_payload).encode("utf-8")
            url = f"{self.base_url}/sa_order/insert"
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "X-MISA-AppID": self.app_id,
                    "Authorization": f"Bearer {self.access_token}",
                    "X-Idempotency-Key": payload.idempotency_key,
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                resp_json = json.loads(response.read().decode("utf-8"))
                voucher_no = resp_json.get("voucher_no") or f"DH-{payload.po_number}"
                return ERPSyncResponse(
                    success=True,
                    transaction_id=voucher_no,
                    adapter_type=ERPAdapterType.MISA_AMIS_LIVE,
                    idempotency_key=payload.idempotency_key,
                    mode="live",
                    timestamp=time.time(),
                    error_message=None,
                )
        except Exception as exc:
            return ERPSyncResponse(
                success=False,
                transaction_id=None,
                adapter_type=ERPAdapterType.MISA_AMIS_LIVE,
                idempotency_key=payload.idempotency_key,
                mode="live",
                timestamp=time.time(),
                error_message=str(exc),
            )

    def fetch_inventory(self, skus: list[str] | None = None) -> list[InventorySnapshot]:
        """Fetch inventory on-hand from MISA AMIS Stock API."""
        from datetime import datetime, timezone
        from decimal import Decimal
        from preflight.models import InventorySnapshot

        now_iso = datetime.now(timezone.utc).isoformat()
        default_map = {
            "LAPTOP-A14": (Decimal("50"), Decimal("0")),
            "MONITOR-27": (Decimal("30"), Decimal("0")),
            "CAB-CAT6-3M": (Decimal("100"), Decimal("0")),
            "HEADSET-PRO": (Decimal("0"), Decimal("0")),
            "KEYBOARD-M1": (Decimal("25"), Decimal("0")),
            "MOUSE-W2": (Decimal("40"), Decimal("0")),
        }
        target_skus = skus if skus is not None else list(default_map.keys())

        if self.dry_run or not self.access_token:
            return [
                InventorySnapshot(
                    sku=s,
                    warehouse="KHO-TONG",
                    on_hand=default_map.get(s, (Decimal("50"), Decimal("0")))[0],
                    reserved=default_map.get(s, (Decimal("50"), Decimal("0")))[1],
                    as_of=now_iso,
                    source="misa_live_dryrun",
                )
                for s in target_skus
            ]

        try:
            url = f"{self.api_url}/inventory/stock_balance"
            req = urllib.request.Request(
                url,
                headers={
                    "Content-Type": "application/json",
                    "X-MISA-AppID": self.app_id,
                    "Authorization": f"Bearer {self.access_token}",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                items = data.get("data", [])
                return [
                    InventorySnapshot(
                        sku=it.get("inventory_item_code", ""),
                        warehouse=it.get("stock_code", "KHO-TONG"),
                        on_hand=Decimal(str(it.get("quantity", 0))),
                        reserved=Decimal(str(it.get("reserved_quantity", 0))),
                        as_of=now_iso,
                        source="misa_live",
                    )
                    for it in items
                ]
        except Exception as exc:
            logger.error(f"Failed to fetch MISA live inventory: {exc}")
            return []

