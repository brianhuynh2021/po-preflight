from __future__ import annotations

from fastapi import APIRouter, Depends

from preflight.api.deps import get_catalog
from preflight.api.schemas import CatalogItemResponse
from preflight.models import Product

router = APIRouter(prefix="/api/v1/catalog", tags=["Product Catalog & Inventory"])


@router.get(
    "",
    response_model=list[CatalogItemResponse],
    summary="List Master Product Catalog",
    description="Retrieve all registered SKUs with official unit prices and real-time inventory counts.",
)
def list_catalog(catalog: dict[str, Product] = Depends(get_catalog)) -> list[CatalogItemResponse]:
    return [
        CatalogItemResponse(
            sku=prod.sku,
            name=prod.name,
            unit_price=prod.unit_price,
            stock=prod.stock,
            active=prod.active,
        )
        for prod in catalog.values()
    ]
