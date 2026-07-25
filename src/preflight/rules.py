from __future__ import annotations

from decimal import Decimal

from preflight.models import Analysis, Finding, Order, Product


def analyze_order(
    order: Order,
    catalog: dict[str, Product],
    *,
    duplicate: bool = False,
    price_tolerance_percent: Decimal = Decimal("0"),
) -> Analysis:
    findings: list[Finding] = []
    if duplicate:
        findings.append(
            Finding(
                code="DUPLICATE_PO",
                severity="error",
                message=f"PO {order.po_number} has already been processed.",
            )
        )

    for item in order.items:
        product = catalog.get(item.sku)
        if product is None:
            findings.append(
                Finding(
                    code="UNKNOWN_SKU",
                    severity="error",
                    sku=item.sku,
                    message=f"SKU {item.sku} does not exist in the catalog.",
                )
            )
            continue
        if not product.active:
            findings.append(
                Finding(
                    code="INACTIVE_SKU",
                    severity="error",
                    sku=item.sku,
                    message=f"SKU {item.sku} is inactive.",
                )
            )
        if item.quantity > product.stock:
            findings.append(
                Finding(
                    code="INSUFFICIENT_STOCK",
                    severity="warning",
                    sku=item.sku,
                    message=(
                        f"SKU {item.sku}: ordered {item.quantity}, only {product.stock} in stock."
                    ),
                )
            )
        if product.unit_price > 0:
            difference = abs(item.unit_price - product.unit_price)
            percent = (difference / product.unit_price) * Decimal("100")
            if percent > price_tolerance_percent:
                findings.append(
                    Finding(
                        code="PRICE_MISMATCH",
                        severity="warning",
                        sku=item.sku,
                        message=(
                            f"SKU {item.sku}: PO price {item.unit_price:,.0f}, "
                            f"catalog price {product.unit_price:,.0f} "
                            f"({percent:.2f}% difference)."
                        ),
                    )
                )

    if any(f.severity == "error" for f in findings):
        status = "blocked"
    elif findings:
        status = "review_required"
    else:
        status = "ready_for_approval"
    return Analysis(order=order, findings=findings, status=status)
