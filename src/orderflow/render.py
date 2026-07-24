from __future__ import annotations

from orderflow.models import Analysis


STATUS_LABELS = {
    "blocked": "BLOCKED",
    "review_required": "REVIEW REQUIRED",
    "ready_for_approval": "READY FOR APPROVAL",
}


def render_markdown(analysis: Analysis) -> str:
    order = analysis.order
    lines = [
        f"# ORDERFLOW - {STATUS_LABELS.get(analysis.status, analysis.status.upper())}",
        "",
        f"- PO: **{order.po_number}**",
        f"- Customer: **{order.customer}**",
        f"- Total: **{order.total:,.0f} {order.currency}**",
        f"- Line items: **{len(order.items)}**",
        "",
        "## Validation results",
    ]
    if not analysis.findings:
        lines.append("- No issues found. The order can be sent for approval.")
    else:
        labels = {"error": "ERROR", "warning": "WARNING", "info": "INFO"}
        for finding in analysis.findings:
            label = labels.get(finding.severity, finding.severity.upper())
            lines.append(f"- [{label}] {finding.message}")
    lines.extend(
        [
            "",
            "## Recommended action",
            (
                "- Ask the sender to correct the order before processing."
                if analysis.status == "blocked"
                else "- Send the order to an authorized reviewer for confirmation."
            ),
            "- Do not create an ERP order before human approval.",
        ]
    )
    return "\n".join(lines)
