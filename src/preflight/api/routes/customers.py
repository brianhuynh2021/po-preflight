from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import StreamingResponse

from preflight.api.deps import get_audit_store
from preflight.api.errors import NotFound, ValidationFailed
from preflight.api.schemas import (
    CustomerCreateRequest,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdateRequest,
)
from preflight.models import CustomerMaster
from preflight.security.rbac import Role, UserPrincipal, require_role
from preflight.services.customer_resolver import normalize_vietnamese_name
from preflight.store import AuditStore


router = APIRouter(prefix="/api/v1/customers", tags=["Customer Master Management"])


@router.get(
    "",
    response_model=list[CustomerResponse],
    summary="List Customer Master Records",
    description="Retrieve all registered customer master entities with search filter and pagination.",
)
def list_customers(
    search: str | None = Query(None, description="Search by name, code, tax code, or alias"),
    limit: int = Query(50, ge=1, le=200, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    store: AuditStore = Depends(get_audit_store),
) -> list[CustomerResponse]:
    customers = store.list_customers(search=search, limit=limit, offset=offset)
    return [
        CustomerResponse(
            id=c.id,
            code=c.code,
            name=c.name,
            normalized_name=c.normalized_name,
            tax_code=c.tax_code,
            tier=c.tier,
            aliases=c.aliases,
            created_at=c.created_at,
        )
        for c in customers
    ]


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=201,
    summary="Create Customer Master Record",
    description="Register a new master customer record with tax code, priority tier, and recognized aliases.",
)
def create_customer(
    req: CustomerCreateRequest,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_audit_store),
) -> CustomerResponse:
    existing = store.get_customer(req.code)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Mã khách hàng '{req.code}' đã tồn tại trong hệ thống.",
        )

    norm_name = normalize_vietnamese_name(req.name)
    cust = CustomerMaster(
        code=req.code.strip(),
        name=req.name.strip(),
        normalized_name=norm_name,
        tax_code=req.tax_code.strip() if req.tax_code else None,
        tier=req.tier.strip().upper(),
        aliases=req.aliases,
    )
    created = store.create_customer(cust)
    return CustomerResponse(
        id=created.id,
        code=created.code,
        name=created.name,
        normalized_name=created.normalized_name,
        tax_code=created.tax_code,
        tier=created.tier,
        aliases=created.aliases,
        created_at=created.created_at,
    )


@router.post(
    "/import-csv",
    summary="Import Customer Master from CSV",
    description="Bulk import customer master registry with aliases (semicolon-separated).",
)
async def import_customers_csv(
    file: UploadFile = File(..., description="CSV file with columns: code,name,tax_code,tier,aliases"),
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_audit_store),
) -> dict[str, Any]:
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    imported = 0
    errors = []

    for idx, row in enumerate(reader, start=2):
        code = row.get("code", "").strip()
        name = row.get("name", "").strip()
        tax_code = row.get("tax_code", "").strip() or None
        tier = row.get("tier", "STANDARD").strip().upper() or "STANDARD"
        aliases_raw = row.get("aliases", "")
        aliases = [a.strip() for a in aliases_raw.split(";") if a.strip()]

        if not code or not name:
            errors.append(f"Dòng {idx}: Thiếu code hoặc name.")
            continue

        existing = store.get_customer(code)
        if existing:
            store.update_customer(code, {"name": name, "tax_code": tax_code, "tier": tier, "aliases": aliases})
        else:
            cust = CustomerMaster(
                code=code,
                name=name,
                normalized_name=normalize_vietnamese_name(name),
                tax_code=tax_code,
                tier=tier,
                aliases=aliases,
            )
            store.create_customer(cust)
        imported += 1

    return {"imported_count": imported, "errors": errors}


@router.get(
    "/export-csv",
    summary="Export Customer Master to CSV",
    description="Export registered customer master database into CSV format.",
)
def export_customers_csv(
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_audit_store),
) -> StreamingResponse:
    customers = store.list_customers(limit=1000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["code", "name", "tax_code", "tier", "aliases"])

    for c in customers:
        aliases_str = ";".join(c.aliases)
        writer.writerow([c.code, c.name, c.tax_code or "", c.tier, aliases_str])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customers_master.csv"},
    )


@router.get(
    "/{customer_code}",
    response_model=CustomerDetailResponse,
    summary="Get Customer Master Details",
    description="Retrieve deep customer profile including contract pricing, credit balance, aliases, and order history.",
)
def get_customer_detail(
    customer_code: str,
    user: UserPrincipal = Depends(require_role(Role.VIEWER)),
    store: AuditStore = Depends(get_audit_store),
) -> CustomerDetailResponse:
    cust = store.get_customer(customer_code)
    if not cust:
        raise NotFound(f"Không tìm thấy khách hàng với mã '{customer_code}'.")

    # Fetch pricing agreements
    pricing_agreements = store.get_customer_pricing(cust.code)
    pricing_data = [
        {
            "sku": p.sku,
            "contract_price": str(p.contract_price),
            "min_quantity": p.min_quantity,
            "discount_percent": str(p.discount_percent),
            "valid_from": p.valid_from,
            "valid_to": p.valid_to,
        }
        for p in pricing_agreements
    ]

    # Fetch credit profile
    credit_profile = store.get_customer_credit(cust.code)
    credit_data = None
    if credit_profile:
        credit_data = {
            "credit_limit": str(credit_profile.credit_limit),
            "outstanding_balance": str(credit_profile.outstanding_balance),
            "overdue_balance": str(credit_profile.overdue_balance),
            "oldest_overdue_days": credit_profile.oldest_overdue_days,
            "status": credit_profile.status,
        }

    # Fetch recent orders
    recent_orders = store.get_recent_customer_orders(cust.name, days=30)

    return CustomerDetailResponse(
        id=cust.id,
        code=cust.code,
        name=cust.name,
        normalized_name=cust.normalized_name,
        tax_code=cust.tax_code,
        tier=cust.tier,
        aliases=cust.aliases,
        created_at=cust.created_at,
        pricing=pricing_data,
        credit=credit_data,
        recent_orders=recent_orders,
    )


@router.put(
    "/{customer_code}",
    response_model=CustomerResponse,
    summary="Update Customer Master Record",
    description="Update legal entity details, tax code, tier, or alias list.",
)
def update_customer(
    customer_code: str,
    req: CustomerUpdateRequest,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_audit_store),
) -> CustomerResponse:
    update_data = req.model_dump(exclude_unset=True)
    updated = store.update_customer(customer_code, update_data)
    if not updated:
        raise NotFound(f"Không tìm thấy khách hàng với mã '{customer_code}'.")

    return CustomerResponse(
        id=updated.id,
        code=updated.code,
        name=updated.name,
        normalized_name=updated.normalized_name,
        tax_code=updated.tax_code,
        tier=updated.tier,
        aliases=updated.aliases,
        created_at=updated.created_at,
    )


@router.delete(
    "/{customer_code}",
    status_code=204,
    summary="Delete Customer Master Record",
    description="Delete customer entity from master registry.",
)
def delete_customer(
    customer_code: str,
    user: UserPrincipal = Depends(require_role(Role.MANAGER)),
    store: AuditStore = Depends(get_audit_store),
) -> Response:
    success = store.delete_customer(customer_code)
    if not success:
        raise NotFound(f"Không tìm thấy khách hàng với mã '{customer_code}'.")
    return Response(status_code=204)
