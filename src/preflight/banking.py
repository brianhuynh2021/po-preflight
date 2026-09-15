"""Manual-input disbursement preflight pilot; no credit decision or payment execution.

Policy BANK-PILOT-1 is illustrative, not a bank-approved lending policy.
All evidence refers to supplied fields, not independently verified documents.
"""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Amount = Annotated[Decimal, Field(ge=0, max_digits=15, decimal_places=0, allow_inf_nan=False)]
PositiveAmount = Annotated[Decimal, Field(gt=0, max_digits=15, decimal_places=0, allow_inf_nan=False)]
DocumentType = Literal["disbursement_request", "credit_agreement", "purchase_contract", "invoice"]
REQUIRED_DOCUMENTS = ("disbursement_request", "credit_agreement", "purchase_contract", "invoice")


class BankingModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Invoice(BankingModel):
    number: Text
    seller_tax_id: Text
    buyer_tax_id: Text
    amount: PositiveAmount
    already_financed: Amount = Decimal("0")
    issued_on: date
    source_reference: Text

    @model_validator(mode="after")
    def check_financed_amount(self):
        if self.already_financed > self.amount:
            raise ValueError("Already financed amount cannot exceed invoice amount")
        return self


class DisbursementCase(BankingModel):
    case_id: Text
    borrower: Text
    borrower_tax_id: Text
    currency: Literal["VND"] = "VND"
    requested_amount: PositiveAmount
    beneficiary_tax_id: Text
    contract_reference: Text
    contract_valid_until: date
    approved_limit: Amount
    outstanding_amount: Amount
    limit_as_of: date
    documents: list[DocumentType] = Field(max_length=4)
    invoices: list[Invoice] = Field(max_length=100)

    @model_validator(mode="after")
    def check_aggregate_amount(self):
        # Keep even aggregate display values within the pilot's 15-digit range.
        if sum((invoice.amount for invoice in self.invoices), Decimal("0")) > Decimal("999999999999999"):
            raise ValueError("Total invoice amount exceeds pilot limit of 15 digits")
        return self


class BankingFinding(BankingModel):
    code: str
    severity: Literal["warning", "error"]
    fields: list[str]
    evidence: dict[str, str]


class DisbursementAnalysis(BankingModel):
    case_id: str
    status: Literal["Ready", "Review required", "Blocked"]
    policy_version: str = "BANK-PILOT-1"
    mode: Literal["pilot_manual_input"] = "pilot_manual_input"
    evaluated_on: date
    available_limit: Decimal
    eligible_invoice_amount: Decimal
    findings: list[BankingFinding]


def analyze_disbursement(case: DisbursementCase, *, as_of: date) -> DisbursementAnalysis:
    """Pure deterministic checks; Ready only means these pilot checks passed."""
    findings: list[BankingFinding] = []

    def add(code, fields, evidence, severity="error"):
        findings.append(BankingFinding(code=code, severity=severity, fields=fields,
                                       evidence={k: str(v) for k, v in evidence.items()}))

    missing = [doc for doc in REQUIRED_DOCUMENTS if doc not in case.documents]
    if missing:
        add("DOCUMENTS_MISSING", ["documents"], {"missing": ", ".join(missing)})
    if case.contract_valid_until < as_of:
        add("CONTRACT_EXPIRED", ["contract_valid_until"],
            {"contract": case.contract_reference, "valid_until": case.contract_valid_until, "as_of": as_of})
    if case.limit_as_of != as_of:
        add("LIMIT_SNAPSHOT_FUTURE" if case.limit_as_of > as_of else "LIMIT_SNAPSHOT_STALE",
            ["limit_as_of"], {"snapshot_date": case.limit_as_of, "as_of": as_of},
            "error" if case.limit_as_of > as_of else "warning")

    available = max(Decimal("0"), case.approved_limit - case.outstanding_amount)
    if case.requested_amount > available:
        add("LIMIT_EXCEEDED", ["requested_amount", "approved_limit", "outstanding_amount"],
            {"requested": case.requested_amount, "available": available})

    eligible = Decimal("0")
    seen: dict[tuple[str, str], int] = {}
    if not case.invoices:
        add("INVOICES_MISSING", ["invoices"], {"invoice_count": 0})
    for index, invoice in enumerate(case.invoices):
        prefix = f"invoices.{index}"
        evidence = {"invoice": invoice.number, "source": invoice.source_reference}
        valid = True
        key = (invoice.seller_tax_id.casefold(), invoice.number.casefold())
        if key in seen:
            add("DUPLICATE_INVOICE", [f"{prefix}.number", f"invoices.{seen[key]}.number"], evidence)
            valid = False
        else:
            seen[key] = index
        for field, expected, code in (
            ("seller_tax_id", case.beneficiary_tax_id, "BENEFICIARY_MISMATCH"),
            ("buyer_tax_id", case.borrower_tax_id, "BORROWER_MISMATCH"),
        ):
            actual = getattr(invoice, field)
            if actual != expected:
                add(code, [f"{prefix}.{field}"], {**evidence, "expected": expected, "actual": actual})
                valid = False
        if invoice.issued_on > as_of:
            add("INVOICE_FUTURE", [f"{prefix}.issued_on"], {**evidence, "issued_on": invoice.issued_on, "as_of": as_of})
            valid = False
        if valid:
            eligible += invoice.amount - invoice.already_financed

    if case.requested_amount > eligible:
        add("INVOICE_BALANCE_EXCEEDED", ["requested_amount", "invoices"],
            {"requested": case.requested_amount, "eligible_invoice_amount": eligible})

    status = "Blocked" if any(f.severity == "error" for f in findings) else "Review required" if findings else "Ready"
    return DisbursementAnalysis(case_id=case.case_id, status=status, evaluated_on=as_of,
                                available_limit=available, eligible_invoice_amount=eligible, findings=findings)
