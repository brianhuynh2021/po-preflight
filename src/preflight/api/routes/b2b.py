from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from preflight.api.deps import get_store
from preflight.models import CustomerCreditProfile, CustomerPriceAgreement, UOMConversion

from preflight.security.rbac import Role, require_role
from preflight.store import BaseAuditStore

router = APIRouter(prefix="/api/v1", tags=["B2B Rules & Masters"])


class CustomerPriceRequest(BaseModel):
    sku: str = Field(..., description="Target SKU")
    contract_price: Decimal = Field(..., description="Agreed unit contract price")
    min_quantity: int = Field(default=1, description="Minimum order quantity for this price bracket")
    discount_percent: Decimal = Field(default=Decimal("0"), description="Volume tier discount percentage")
    valid_from: Optional[str] = Field(default=None, description="Start date ISO-8601")
    valid_to: Optional[str] = Field(default=None, description="End date ISO-8601")


class CustomerCreditRequest(BaseModel):
    credit_limit: Decimal = Field(..., description="Approved total credit limit in VND")
    outstanding_balance: Decimal = Field(default=Decimal("0"), description="Current unpaid balance in VND")
    overdue_balance: Decimal = Field(default=Decimal("0"), description="Total overdue debt in VND")
    oldest_overdue_days: int = Field(default=0, description="Age in days of oldest unpaid invoice")
    status: str = Field(default="ACTIVE", description="ACTIVE, ON_HOLD, or BLOCKED")


class UOMConversionRequest(BaseModel):
    sku: str = Field(..., description="Target SKU")
    uom_code: str = Field(..., description="Packaging UOM code (e.g. CARTON, BOX, ROLL)")
    base_uom: str = Field(default="PCS", description="Base inventory unit (e.g. PCS)")
    conversion_factor: Decimal = Field(..., description="Multiplier to base units (e.g. 1 CARTON = 20 PCS -> 20.0)")


# -------------------------------------------------------------------
# Customer Contract Pricing Endpoints (Issue #72)
# -------------------------------------------------------------------

@router.post(
    "/customers/{customer_id}/prices",
    status_code=status.HTTP_201_CREATED,
    summary="Set or update customer contract price bracket",
    dependencies=[Depends(require_role(Role.MANAGER))],
)
def set_customer_pricing(
    customer_id: str,
    payload: CustomerPriceRequest,
    store: BaseAuditStore = Depends(get_store),
) -> dict[str, Any]:
    agreement = CustomerPriceAgreement(
        customer_id=customer_id,
        sku=payload.sku,
        contract_price=payload.contract_price,
        min_quantity=payload.min_quantity,
        discount_percent=payload.discount_percent,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
    )
    store.set_customer_pricing(agreement)
    return {
        "status": "success",
        "message": f"Contract price for customer '{customer_id}' and SKU '{payload.sku}' registered.",
        "pricing": agreement.to_dict(),
    }


@router.get(
    "/customers/{customer_id}/prices",
    summary="Get all contract pricing agreements for customer",
    dependencies=[Depends(require_role(Role.VIEWER))],
)
def get_customer_pricing(
    customer_id: str,
    store: BaseAuditStore = Depends(get_store),
) -> list[dict[str, Any]]:
    agreements = store.get_customer_pricing(customer_id)
    return [a.to_dict() for a in agreements]


# -------------------------------------------------------------------
# Customer Credit & Risk Endpoints (Issue #74)
# -------------------------------------------------------------------

@router.post(
    "/customers/{customer_id}/credit",
    status_code=status.HTTP_200_OK,
    summary="Set or update customer financial credit profile",
    dependencies=[Depends(require_role(Role.MANAGER))],
)
def set_customer_credit(
    customer_id: str,
    payload: CustomerCreditRequest,
    store: BaseAuditStore = Depends(get_store),
) -> dict[str, Any]:
    profile = CustomerCreditProfile(
        customer_id=customer_id,
        credit_limit=payload.credit_limit,
        outstanding_balance=payload.outstanding_balance,
        overdue_balance=payload.overdue_balance,
        oldest_overdue_days=payload.oldest_overdue_days,
        status=payload.status.upper(),
    )
    store.set_customer_credit(profile)
    return {
        "status": "success",
        "message": f"Credit profile for customer '{customer_id}' updated.",
        "profile": profile.to_dict(),
    }


@router.get(
    "/customers/{customer_id}/credit",
    summary="Get financial credit profile for customer",
    dependencies=[Depends(require_role(Role.VIEWER))],
)
def get_customer_credit(
    customer_id: str,
    store: BaseAuditStore = Depends(get_store),
) -> dict[str, Any]:
    profile = store.get_customer_credit(customer_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credit profile for customer '{customer_id}' not found.",
        )
    return profile.to_dict()


# -------------------------------------------------------------------
# UOM Conversion Matrix Endpoints (Issue #73)
# -------------------------------------------------------------------

@router.post(
    "/uom/conversions",
    status_code=status.HTTP_201_CREATED,
    summary="Set or update Unit of Measure (UOM) conversion rule",
    dependencies=[Depends(require_role(Role.MANAGER))],
)
def set_uom_conversion(
    payload: UOMConversionRequest,
    store: BaseAuditStore = Depends(get_store),
) -> dict[str, Any]:
    conversion = UOMConversion(
        sku=payload.sku,
        uom_code=payload.uom_code,
        base_uom=payload.base_uom,
        conversion_factor=payload.conversion_factor,
    )
    store.set_uom_conversion(conversion)
    return {
        "status": "success",
        "message": f"UOM conversion for SKU '{payload.sku}' ({payload.uom_code} -> {payload.conversion_factor} {payload.base_uom}) registered.",
        "conversion": conversion.to_dict(),
    }



@router.get(
    "/uom/conversions",
    summary="List UOM conversion matrix",
    dependencies=[Depends(require_role(Role.VIEWER))],
)
def get_uom_conversions(
    sku: Optional[str] = Query(None, description="Filter by SKU"),
    store: BaseAuditStore = Depends(get_store),
) -> list[dict[str, Any]]:
    conversions = store.get_uom_conversions(sku)
    return [c.to_dict() for c in conversions]
