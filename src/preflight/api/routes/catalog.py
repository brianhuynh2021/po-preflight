from __future__ import annotations

import csv
import io
import shutil
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from preflight.api.deps import get_audit_store, get_catalog, get_catalog_path
from preflight.api.errors import ValidationFailed
from preflight.api.schemas import CatalogItemResponse
from preflight.catalog import invalidate_catalog_cache
from preflight.models import Product
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.store import BaseAuditStore

router = APIRouter(prefix="/api/v1/catalog", tags=["Product Catalog & Inventory"])


@router.get(
    "",
    response_model=list[CatalogItemResponse],
    summary="List Master Product Catalog",
    description="Retrieve all registered SKUs with official unit prices, base UOM, MOQ, pack sizes, and real-time inventory counts and ATP.",
)
def list_catalog(
    catalog: dict[str, Product] = Depends(get_catalog),
    store: BaseAuditStore = Depends(get_audit_store),
) -> list[CatalogItemResponse]:
    items: list[CatalogItemResponse] = []
    for prod in catalog.values():
        atp_info = store.calculate_atp(prod.sku, catalog_stock=prod.stock)
        items.append(
            CatalogItemResponse(
                sku=prod.sku,
                name=prod.name,
                unit_price=prod.unit_price,
                stock=prod.stock,
                active=prod.active,
                base_uom=prod.base_uom,
                moq=prod.moq,
                pack_size=prod.pack_size,
                category=prod.category,
                barcode=prod.barcode,
                on_hand=atp_info.get("on_hand"),
                reserved_erp=atp_info.get("reserved_erp"),
                allocated_local=atp_info.get("allocated_local"),
                atp=atp_info.get("atp"),
                as_of=atp_info.get("as_of"),
                is_stale=atp_info.get("is_stale", False),
            )
        )
    return items


@router.post(
    "/import",
    summary="Import Catalog CSV",
    description="Validate and import a new product master catalog CSV file (ADMIN only).",
)
async def import_catalog_csv(
    file: UploadFile = File(...),
    principal: UserPrincipal = Depends(require_role(Role.ADMIN)),
    store: BaseAuditStore = Depends(get_audit_store),
) -> dict[str, object]:
    content_bytes = await file.read()
    try:
        content_text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValidationFailed(
            "Tệp CSV không đúng định dạng mã hóa UTF-8",
            errors=[{"row": 0, "column": "file", "message": f"Lỗi giải mã: {exc}"}],
        ) from exc

    handle = io.StringIO(content_text)
    reader = csv.DictReader(handle)
    if not reader.fieldnames:
        raise ValidationFailed(
            "Tệp catalog rỗng hoặc thiếu tiêu đề cột",
            errors=[{"row": 1, "column": "header", "message": "Header rỗng hoặc không có cột hợp lệ"}],
        )

    field_map = {f.strip().lower(): f for f in reader.fieldnames if f}
    required_fields = ["sku", "name", "unit_price", "stock"]
    missing_required = [rf for rf in required_fields if rf not in field_map]
    if missing_required:
        raise ValidationFailed(
            f"Tệp catalog thiếu các cột bắt buộc: {', '.join(missing_required)}",
            errors=[
                {"row": 1, "column": col, "message": f"Cột bắt buộc '{col}' bị thiếu"}
                for col in missing_required
            ],
        )

    errors: list[dict[str, object]] = []
    valid_products: list[Product] = []
    line_no = 1

    for raw_row in reader:
        line_no += 1
        row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items() if k}

        sku = row.get("sku", "").upper()
        if not sku:
            errors.append({"row": line_no, "column": "sku", "message": "Cột 'sku' không được để trống"})

        name = row.get("name", "")
        if not name:
            errors.append({"row": line_no, "column": "name", "message": "Cột 'name' không được để trống"})

        raw_price = row.get("unit_price", "")
        unit_price = Decimal("0")
        try:
            unit_price = Decimal(raw_price.replace(",", ""))
            if unit_price < 0:
                errors.append({"row": line_no, "column": "unit_price", "message": "Giá đơn vị không được âm"})
        except (InvalidOperation, ValueError):
            errors.append({"row": line_no, "column": "unit_price", "message": f"Giá '{raw_price}' không hợp lệ"})

        raw_stock = row.get("stock", "")
        stock = 0
        try:
            stock = int(raw_stock)
            if stock < 0:
                errors.append({"row": line_no, "column": "stock", "message": "Tồn kho không được âm"})
        except ValueError:
            errors.append({"row": line_no, "column": "stock", "message": f"Tồn kho '{raw_stock}' phải là số nguyên >= 0"})

        raw_active = row.get("active", "true").lower()
        active = raw_active in {"1", "true", "yes", "active"}

        base_uom = row.get("base_uom", "PCS").upper() or "PCS"

        raw_moq = row.get("moq", "1") or "1"
        moq = 1
        try:
            moq = int(raw_moq)
            if moq < 1:
                errors.append({"row": line_no, "column": "moq", "message": "MOQ phải >= 1"})
        except ValueError:
            errors.append({"row": line_no, "column": "moq", "message": f"MOQ '{raw_moq}' phải là số nguyên >= 1"})

        raw_pack = row.get("pack_size", "1") or "1"
        pack_size = 1
        try:
            pack_size = int(raw_pack)
            if pack_size < 1:
                errors.append({"row": line_no, "column": "pack_size", "message": "Pack size phải >= 1"})
        except ValueError:
            errors.append({"row": line_no, "column": "pack_size", "message": f"Pack size '{raw_pack}' phải là số nguyên >= 1"})

        category = row.get("category") or None
        barcode = row.get("barcode") or None

        if sku and name:
            valid_products.append(
                Product(
                    sku=sku,
                    name=name,
                    unit_price=unit_price,
                    stock=stock,
                    active=active,
                    base_uom=base_uom,
                    moq=moq,
                    pack_size=pack_size,
                    category=category,
                    barcode=barcode,
                )
            )

    if errors:
        raise ValidationFailed(
            f"Tệp catalog chứa {len(errors)} lỗi xác thực",
            errors=errors,
        )

    if not valid_products:
        raise ValidationFailed(
            "Tệp catalog không có dòng sản phẩm hợp lệ nào",
            errors=[{"row": 1, "column": "data", "message": "Không có dữ liệu"}],
        )

    # All validations passed: safely backup old catalog and write new catalog
    target_path = get_catalog_path()
    if target_path.exists():
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        backup_path = target_path.with_name(f"{target_path.name}.{timestamp_str}.bak")
        shutil.copy2(target_path, backup_path)

    # Write new CSV content
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(content_bytes)

    # Invalidate cache
    invalidate_catalog_cache(target_path)

    # Record audit event
    store.append_audit_block(
        "CATALOG",
        "CATALOG_IMPORTED",
        principal.username,
        {
            "filename": file.filename,
            "total_skus": len(valid_products),
            "imported_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {
        "success": True,
        "message": f"Đã nhập thành công {len(valid_products)} sản phẩm vào catalog.",
        "total_skus": len(valid_products),
    }
