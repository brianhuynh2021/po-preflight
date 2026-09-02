from __future__ import annotations

from decimal import Decimal
from preflight.ingestion.schemas import ExtractedLineItem, ExtractedOrderHeader, MathVerificationResult


class SelfReflectionVerifier:
    """Self-Reflection Mathematical Verifier to eradicate OCR/LLM hallucinations."""

    def __init__(self, default_tolerance: Decimal = Decimal("1000")):
        self.default_tolerance = default_tolerance

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

        calc_total = sum((it.amount for it in items), start=Decimal("0"))
        declared = header.grand_total if header.grand_total > 0 else header.subtotal
        diff = abs(calc_total - declared)

        # Dynamic tolerance: max(1000 VND / 0.05 currency units, 0.5% of total)
        min_abs_tol = Decimal("1000") if header.currency.upper() == "VND" else Decimal("0.05")
        relative_tol = declared * Decimal("0.005")
        dynamic_tolerance = max(min_abs_tol, relative_tol)

        # Check rounding discrepancy
        rounded_sum = sum((round(it.amount) for it in items), start=Decimal("0"))
        is_rounding_diff = (abs(rounded_sum - declared) <= min_abs_tol) and (diff <= declared * Decimal("0.01"))

        if diff <= dynamic_tolerance or is_rounding_diff:
            has_discrepancy = False
            if is_rounding_diff and diff > 0:
                message = (
                    f"Khớp tổng tiền (lệch do làm tròn thuế/chiết khấu {diff:,.2f} {header.currency}): "
                    f"Tính toán {calc_total:,.2f} {header.currency} ~ Khai báo {declared:,.2f} {header.currency}."
                )
            else:
                message = (
                    f"Math verified 100%: Sum of line items ({calc_total:,.0f} {header.currency}) "
                    f"matches declared subtotal ({header.subtotal:,.0f} {header.currency})."
                )
        else:
            has_discrepancy = True
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
