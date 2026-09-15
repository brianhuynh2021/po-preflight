from copy import deepcopy
from datetime import date
import unittest

from pydantic import ValidationError

from preflight.banking import DisbursementCase, analyze_disbursement


def case_data():
    return {
        "case_id": "GN-001", "borrower": "Example Company", "borrower_tax_id": "0101234567",
        "requested_amount": "80000000", "beneficiary_tax_id": "0301234567",
        "contract_reference": "HD-001", "contract_valid_until": "2026-12-31",
        "approved_limit": "100000000", "outstanding_amount": "20000000",
        "limit_as_of": "2026-09-15",
        "documents": ["disbursement_request", "credit_agreement", "purchase_contract", "invoice"],
        "invoices": [{"number": "INV-001", "seller_tax_id": "0301234567",
                      "buyer_tax_id": "0101234567", "amount": "90000000",
                      "already_financed": "10000000", "issued_on": "2026-09-01",
                      "source_reference": "invoice.pdf / page 1"}],
    }


class BankingRulesTests(unittest.TestCase):
    def analyze(self, data):
        return analyze_disbursement(DisbursementCase.model_validate(data), as_of=date(2026, 9, 15))

    def test_exact_boundaries_ready_and_never_approved(self):
        result = self.analyze(case_data())
        self.assertEqual(result.status, "Ready")
        self.assertEqual(result.available_limit, 80000000)
        self.assertEqual(result.eligible_invoice_amount, 80000000)
        self.assertEqual(result.findings, [])
        self.assertEqual(result.mode, "pilot_manual_input")

    def test_over_limit_and_invoice_balance_block_with_evidence(self):
        data = case_data()
        data["requested_amount"] = "80000001"
        result = self.analyze(data)
        self.assertEqual(result.status, "Blocked")
        self.assertEqual({f.code for f in result.findings}, {"LIMIT_EXCEEDED", "INVOICE_BALANCE_EXCEEDED"})
        self.assertTrue(all(f.evidence and f.fields for f in result.findings))

    def test_missing_documents_and_empty_invoices_block(self):
        data = case_data()
        data["documents"] = []
        data["invoices"] = []
        codes = {f.code for f in self.analyze(data).findings}
        self.assertIn("DOCUMENTS_MISSING", codes)
        self.assertIn("INVOICES_MISSING", codes)

    def test_duplicate_invoice_not_counted_twice(self):
        data = case_data()
        duplicate = deepcopy(data["invoices"][0])
        duplicate["number"] = " inv-001 "
        data["invoices"].append(duplicate)
        result = self.analyze(data)
        self.assertEqual(result.eligible_invoice_amount, 80000000)
        self.assertIn("DUPLICATE_INVOICE", {f.code for f in result.findings})

    def test_mismatched_parties_and_future_invoice_are_ineligible(self):
        for field, value, code in [("seller_tax_id", "999", "BENEFICIARY_MISMATCH"),
                                   ("buyer_tax_id", "999", "BORROWER_MISMATCH"),
                                   ("issued_on", "2026-09-16", "INVOICE_FUTURE")]:
            with self.subTest(field=field):
                data = case_data()
                data["invoices"][0][field] = value
                result = self.analyze(data)
                self.assertEqual(result.eligible_invoice_amount, 0)
                self.assertIn(code, {f.code for f in result.findings})

    def test_stale_limit_requires_review_future_snapshot_blocks(self):
        data = case_data()
        data["limit_as_of"] = "2026-09-14"
        self.assertEqual(self.analyze(data).status, "Review required")
        data["limit_as_of"] = "2026-09-16"
        self.assertEqual(self.analyze(data).status, "Blocked")

    def test_expired_contract_blocks_valid_on_expiry_date(self):
        data = case_data()
        data["contract_valid_until"] = "2026-09-15"
        self.assertEqual(self.analyze(data).status, "Ready")
        data["contract_valid_until"] = "2026-09-14"
        self.assertIn("CONTRACT_EXPIRED", {f.code for f in self.analyze(data).findings})

    def test_invalid_amounts_currency_and_overfinancing_rejected(self):
        for value in ["NaN", "Infinity", "-1", "0", "0.5", "1000000000000000"]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                data = case_data()
                data["requested_amount"] = value
                DisbursementCase.model_validate(data)
        data = case_data()
        data["currency"] = "USD"
        with self.assertRaises(ValidationError):
            DisbursementCase.model_validate(data)
        data = case_data()
        data["invoices"][0]["already_financed"] = "90000001"
        with self.assertRaises(ValidationError):
            DisbursementCase.model_validate(data)

    def test_serialization_preserves_decimal_strings_and_input_is_unchanged(self):
        data = case_data()
        original = deepcopy(data)
        result = self.analyze(data)
        self.assertEqual(result.model_dump(mode="json")["available_limit"], "80000000")
        self.assertEqual(data, original)

    def test_aggregate_stays_within_frontend_exact_integer_range(self):
        data = case_data()
        data["invoices"][0]["amount"] = "999999999999999"
        data["invoices"].append(deepcopy(data["invoices"][0]))
        with self.assertRaises(ValidationError):
            DisbursementCase.model_validate(data)


if __name__ == "__main__":
    unittest.main()
