from __future__ import annotations

from decimal import Decimal
from preflight.ingestion.schemas import ExtractedLineItem, ExtractedOrderHeader, MathVerificationResult


class SelfReflectionVerifier:
    """Self-Reflection Mathematical Verifier to eradicate OCR/LLM hallucinations."""

    def __init__(self, tolerance: Decimal = Decimal("1000")):
        self.tolerance = tolerance

    def verify(
        self,
        header: ExtractedOrderHeader,
        items: list[ExtractedLineItem],
    ) -> MathVerificationResult:
        if not items:
            return MathVerificationResult(
                is_valid=False,
                calculated_items_total=Decimal("0"),
                declared_subtotal=header.subtotal,
                difference=header.subtotal,
                discrepancy_detected=True,
                message="No line items extracted from document.",
            )

        calc_total = Decimal("0")
        for it in items:
            calc_total += it.quantity * it.unit_price

        diff = abs(calc_total - header.subtotal)
        has_discrepancy = diff > self.tolerance

        if not has_discrepancy:
            message = (
                f"Math verified 100%: Sum of line items ({calc_total:,.0f} {header.currency}) "
                f"matches declared subtotal ({header.subtotal:,.0f} {header.currency})."
            )
        else:
            message = (
                f"Math discrepancy detected: Sum of line items ({calc_total:,.0f} {header.currency}) "
                f"differs from declared subtotal ({header.subtotal:,.0f} {header.currency}) by {diff:,.0f} {header.currency}."
            )

        return MathVerificationResult(
            is_valid=not has_discrepancy,
            calculated_items_total=calc_total,
            declared_subtotal=header.subtotal,
            difference=diff,
            discrepancy_detected=has_discrepancy,
            message=message,
        )
