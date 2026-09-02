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
