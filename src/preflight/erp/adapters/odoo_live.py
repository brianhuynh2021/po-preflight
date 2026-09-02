from __future__ import annotations

import logging
import os
import time
import xmlrpc.client
from typing import Any

from preflight.erp.adapters.base import BaseERPAdapter
from preflight.erp.exceptions import ERPConfigurationError
from preflight.erp.schemas import ERPAdapterType, ERPSyncPayload, ERPSyncResponse

logger = logging.getLogger("PreflightOdooLiveAdapter")


class OdooLiveAdapter(BaseERPAdapter):
    """Production Odoo ERP Adapter communicating via XML-RPC / JSON-RPC to sale.order."""

    adapter_type = ERPAdapterType.ODOO_LIVE

    def __init__(
        self,
        url: str | None = None,
        db: str | None = None,
        username: str | None = None,
        password: str | None = None,
        dry_run: bool = False,
    ):
        self.url = url or os.getenv("ODOO_URL", "https://odoo.enterprise.internal")
        self.db = db or os.getenv("ODOO_DB", "production_db")
        self.username = username or os.getenv("ODOO_USER", "admin")
        self.password = password or os.getenv("ODOO_PASSWORD", "")
        self.dry_run = dry_run or os.getenv("ODOO_DRY_RUN", "true").lower() == "true"

    def sync_order(self, payload: ERPSyncPayload) -> ERPSyncResponse:
        """Create Odoo sale.order and order lines with customer partner mapping."""
        # Simulated/Dry-run fallback if no live credentials
        if self.dry_run or not self.password:
            if os.getenv("PREFLIGHT_ENV") == "production":
                raise ERPConfigurationError("Odoo credentials missing in production environment.")

            logger.warning(f"Odoo live adapter running in dry_run mode for PO '{payload.po_number}'")
            clean_digits = "".join(filter(str.isdigit, payload.po_number)) or "1001"
            odoo_id = f"DRYRUN-SO/2026/{clean_digits.zfill(4)}"
            return ERPSyncResponse(
                success=True,
                transaction_id=odoo_id,
                adapter_type=ERPAdapterType.ODOO_LIVE,
                idempotency_key=payload.idempotency_key,
                mode="dry_run",
                timestamp=time.time(),
                error_message=None,
            )

        try:
            # 1. Authenticate via XML-RPC Common Endpoint
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            uid = common.authenticate(self.db, self.username, self.password, {})
            if not uid:
                raise ConnectionError(f"Odoo authentication failed for user '{self.username}' on DB '{self.db}'")

            models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

            # 2. Lookup or create Partner
            partner_ids = models.execute_kw(
                self.db,
                uid,
                self.password,
                "res.partner",
                "search",
                [[["name", "=", payload.customer]]],
            )
            if partner_ids:
                partner_id = partner_ids[0]
            else:
                partner_id = models.execute_kw(
                    self.db,
                    uid,
                    self.password,
                    "res.partner",
                    "create",
                    [{"name": payload.customer, "customer_rank": 1}],
                )

            # 3. Prepare Order Lines
            order_lines = []
            for item in payload.items:
                order_lines.append(
                    (
                        0,
                        0,
                        {
                            "name": f"[{item.get('sku')}] {item.get('description', '')}",
                            "product_uom_qty": float(item.get("quantity", 1)),
                            "price_unit": float(item.get("unit_price", 0)),
                        },
                    )
                )

            # 4. Create Sale Order
            so_id = models.execute_kw(
                self.db,
                uid,
                self.password,
                "sale.order",
                "create",
                [
                    {
                        "partner_id": partner_id,
                        "client_order_ref": payload.po_number,
                        "origin": f"PO-Preflight:{payload.idempotency_key[:8]}",
                        "order_line": order_lines,
                    }
                ],
            )

            # 5. Read back generated Name (e.g. SO0012)
            so_record = models.execute_kw(
                self.db,
                uid,
                self.password,
                "sale.order",
                "read",
                [[so_id]],
                {"fields": ["name"]},
            )
            so_name = so_record[0]["name"] if so_record else f"SO-{so_id}"

            return ERPSyncResponse(
                success=True,
                transaction_id=so_name,
                adapter_type=ERPAdapterType.ODOO_LIVE,
                idempotency_key=payload.idempotency_key,
                mode="live",
                timestamp=time.time(),
                error_message=None,
            )
        except Exception as exc:
            return ERPSyncResponse(
                success=False,
                transaction_id=None,
                adapter_type=ERPAdapterType.ODOO_LIVE,
                idempotency_key=payload.idempotency_key,
                mode="live",
                timestamp=time.time(),
                error_message=str(exc),
            )

    def fetch_inventory(self, skus: list[str] | None = None) -> list[InventorySnapshot]:
        """Fetch stock on-hand and reserved quantity from Odoo stock.quant."""
        from datetime import datetime, timezone
        from decimal import Decimal
        from preflight.models import InventorySnapshot

        now_iso = datetime.now(timezone.utc).isoformat()

        if self.dry_run or not self.password:
            # Simulated stock levels in dry run
            default_map = {
                "LAPTOP-A14": (Decimal("50"), Decimal("0")),
                "MONITOR-27": (Decimal("30"), Decimal("0")),
                "CAB-CAT6-3M": (Decimal("100"), Decimal("0")),
                "HEADSET-PRO": (Decimal("0"), Decimal("0")),
                "KEYBOARD-M1": (Decimal("25"), Decimal("0")),
                "MOUSE-W2": (Decimal("40"), Decimal("0")),
            }
            target_skus = skus if skus is not None else list(default_map.keys())
            return [
                InventorySnapshot(
                    sku=s,
                    warehouse="WH-STOCK",
                    on_hand=default_map.get(s, (Decimal("50"), Decimal("0")))[0],
                    reserved=default_map.get(s, (Decimal("50"), Decimal("0")))[1],
                    as_of=now_iso,
                    source="odoo_live_dryrun",
                )
                for s in target_skus
            ]

        try:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            uid = common.authenticate(self.db, self.username, self.password, {})
            models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

            domain = [["location_id.usage", "=", "internal"]]
            if skus:
                domain.append(["product_id.default_code", "in", skus])

            quants = models.execute_kw(
                self.db,
                uid,
                self.password,
                "stock.quant",
                "search_read",
                [domain],
                {"fields": ["product_id", "quantity", "reserved_quantity", "location_id"]},
            )

            results: dict[str, dict[str, Any]] = {}
            for q in quants:
                prod = q.get("product_id")
                sku_code = prod[1] if isinstance(prod, (list, tuple)) else str(prod)
                # Parse [SKU] name if present
                if "[" in sku_code and "]" in sku_code:
                    sku_code = sku_code.split("]")[0].replace("[", "").strip()

                if sku_code not in results:
                    results[sku_code] = {"on_hand": Decimal("0"), "reserved": Decimal("0")}
                results[sku_code]["on_hand"] += Decimal(str(q.get("quantity", 0)))
                results[sku_code]["reserved"] += Decimal(str(q.get("reserved_quantity", 0)))

            return [
                InventorySnapshot(
                    sku=sku_code,
                    warehouse="WH-STOCK",
                    on_hand=vals["on_hand"],
                    reserved=vals["reserved"],
                    as_of=now_iso,
                    source="odoo_live",
                )
                for sku_code, vals in results.items()
            ]
        except Exception as exc:
            logger.error(f"Failed to fetch Odoo live inventory: {exc}")
            return []

