from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from preflight.models import Order, LineItem


def compute_order_diff(old_order: Order | dict[str, Any], new_order: Order | dict[str, Any]) -> dict[str, Any]:
    """Compute structured line-item and total diffs between two order revisions.
    
    Returns:
    {
        "changes": list[str],  # human-readable changes e.g. ["LAPTOP-A14: 10 → 8"]
        "summary": str,        # one-line summary
        "old_total": str,
        "new_total": str,
        "added_skus": list[str],
        "removed_skus": list[str],
        "modified_skus": list[dict[str, Any]],
    }
    """
    def _extract_items(ord_obj: Order | dict[str, Any]) -> dict[str, dict[str, Any]]:
        if isinstance(ord_obj, Order):
            return {
                item.sku: {
                    "sku": item.sku,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "uom": item.uom,
                }
                for item in ord_obj.items
            }
        items_raw = ord_obj.get("items", [])
        res = {}
        for it in items_raw:
            sku = it.get("sku") or it.get("raw_sku") or "UNKNOWN"
            res[sku] = {
                "sku": sku,
                "quantity": int(it.get("quantity", 1)),
                "unit_price": Decimal(str(it.get("unit_price", 0))),
                "uom": it.get("uom", "PCS"),
            }
        return res

    def _extract_total(ord_obj: Order | dict[str, Any]) -> Decimal:
        if isinstance(ord_obj, Order):
            return ord_obj.total
        return Decimal(str(ord_obj.get("total") or ord_obj.get("grand_total") or 0))

    old_items = _extract_items(old_order)
    new_items = _extract_items(new_order)
    old_total = _extract_total(old_order)
    new_total = _extract_total(new_order)

    changes: list[str] = []
    added_skus: list[str] = []
    removed_skus: list[str] = []
    modified_skus: list[dict[str, Any]] = []

    all_skus = set(old_items.keys()) | set(new_items.keys())
    for sku in sorted(all_skus):
        if sku not in old_items:
            it = new_items[sku]
            changes.append(f"+ {sku}: thêm mới {it['quantity']} {it['uom']}")
            added_skus.append(sku)
        elif sku not in new_items:
            it = old_items[sku]
            changes.append(f"- {sku}: đã xóa (cũ: {it['quantity']} {it['uom']})")
            removed_skus.append(sku)
        else:
            old_it = old_items[sku]
            new_it = new_items[sku]
            sku_changes = []
            if old_it["quantity"] != new_it["quantity"]:
                sku_changes.append(f"{sku}: {old_it['quantity']} → {new_it['quantity']}")
            if old_it["unit_price"] != new_it["unit_price"]:
                sku_changes.append(f"{sku} giá: {old_it['unit_price']:,.0f} → {new_it['unit_price']:,.0f}")
            if sku_changes:
                changes.extend(sku_changes)
                modified_skus.append({
                    "sku": sku,
                    "old_quantity": old_it["quantity"],
                    "new_quantity": new_it["quantity"],
                    "old_unit_price": str(old_it["unit_price"]),
                    "new_unit_price": str(new_it["unit_price"]),
                })

    if not changes:
        if old_total != new_total:
            changes.append(f"Tổng tiền thay đổi: {old_total:,.0f} → {new_total:,.0f}")
        else:
            changes.append("Không có thay đổi dòng hàng.")

    summary = "; ".join(changes)
    return {
        "changes": changes,
        "summary": summary,
        "old_total": str(old_total),
        "new_total": str(new_total),
        "added_skus": added_skus,
        "removed_skus": removed_skus,
        "modified_skus": modified_skus,
    }
