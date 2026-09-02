from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, Depends, Query

from preflight.api.deps import get_audit_store, get_catalog
from preflight.api.schemas import InventorySnapshotResponse
from preflight.erp import get_erp_adapter
from preflight.models import Product
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import BaseAuditStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory & ATP"])


@router.get(
    "/snapshots",
    response_model=list[InventorySnapshotResponse],
    summary="List Inventory Snapshots & ATP",
    description="Retrieve latest inventory snapshots with ATP (Available to Promise) calculations and local allocations.",
)
def list_inventory_snapshots(
    skus: list[str] | None = Query(None, description="Optional list of SKUs to filter"),
    store: BaseAuditStore = Depends(get_audit_store),
    catalog: dict[str, Product] = Depends(get_catalog),
) -> list[InventorySnapshotResponse]:
    target_skus = skus if skus else list(catalog.keys())
    results: list[InventorySnapshotResponse] = []
    
    for sku in target_skus:
        prod = catalog.get(sku)
        catalog_stock = prod.stock if prod else 0
        atp_info = store.calculate_atp(sku, catalog_stock=catalog_stock)
        results.append(
            InventorySnapshotResponse(
                sku=sku,
                warehouse=atp_info.get("warehouse", "DEFAULT"),
                on_hand=atp_info.get("on_hand", 0),
                reserved=atp_info.get("reserved_erp", 0),
                as_of=atp_info.get("as_of", ""),
                source=atp_info.get("source", "catalog"),
                allocated_local=atp_info.get("allocated_local", 0),
                atp=atp_info.get("atp", 0),
                is_stale=atp_info.get("is_stale", False),
            )
        )
    return results


@router.post(
    "/sync",
    summary="Sync Inventory from ERP",
    description="Fetch real-time stock balances from configured ERP (Odoo, SAP, MISA) and record snapshots (SALES_ADMIN or above).",
)
def sync_inventory(
    adapter_type: str | None = Query(None, description="ERP adapter type: odoo, sap, misa_amis, mock_odoo, mock_sap"),
    skus: list[str] | None = Query(None, description="Optional list of SKUs to sync"),
    store: BaseAuditStore = Depends(get_audit_store),
    catalog: dict[str, Product] = Depends(get_catalog),
    principal: UserPrincipal = Depends(require_role(Role.SALES_ADMIN)),
) -> dict[str, Any]:
    adapter = get_erp_adapter(adapter_type)
    target_skus = skus if skus else list(catalog.keys())
    
    snapshots = adapter.fetch_inventory(skus=target_skus)
    count = store.record_inventory_snapshots(snapshots)
    
    # Also record audit event
    store.append_audit_block(
        "INVENTORY",
        "INVENTORY_SYNCED",
        principal.username,
        {
            "adapter": adapter.adapter_type.value,
            "synced_count": count,
            "skus": [s.sku for s in snapshots],
        },
    )

    return {
        "success": True,
        "adapter": adapter.adapter_type.value,
        "count": count,
        "snapshots": [
            {
                "sku": s.sku,
                "warehouse": s.warehouse,
                "on_hand": str(s.on_hand),
                "reserved": str(s.reserved),
                "as_of": s.as_of,
                "source": s.source,
            }
            for s in snapshots
        ],
    }
