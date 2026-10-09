# Banking Preflight — Corporate disbursement pre-check pilot

## Implemented scope

Open `/banking` from the **Hồ sơ giải ngân** (disbursement cases) menu item. The module accepts
manually entered data, runs deterministic rules on the backend and displays errors together with
the evidence used for cross-checking. The `BANK-PILOT-1` rule set is an illustrative assumption;
it is not the credit policy of any bank.

### Try it out

1. Run the backend with the existing login configuration:
   `.venv/bin/python -m uvicorn preflight.api.app:app --app-dir src --host 127.0.0.1 --port 8001`.
2. From `apps/web`, run `npm run dev`, log in to the portal and open `/banking`.
   To disable the debug inspector when testing locally:
   `PREFLIGHT_DISABLE_INSPECTOR=1 npm run dev -- --hostname 127.0.0.1 --port 5187`.
3. Select **Nạp hồ sơ mẫu** (load sample case), then **Kiểm tra hồ sơ** (check case).
4. The sample requests VND 850 million; the remaining limit and the remaining invoice value are both
   VND 800 million. The result must be `Blocked`, with two over-value errors.
5. Change the request to VND 800 million and check again: `Ready`.
6. Untick **Hợp đồng mua bán** (purchase contract): `Blocked`. With all documents present and a
   request of VND 800 million, set the limit date back to yesterday: `Review required`.
7. Open **Xem căn cứ đối chiếu** (view cross-check evidence), or download the case and result as JSON.

The sample limit and invoice dates use the current date in Vietnam. The case lives in page memory
and is lost on reload. Editing the data clears the previous result. API errors are displayed, not
simulated as success. The module does not call AI, store cases, send bot messages or write to core banking.

## BANK-PILOT-1 rules

| Code | Condition | Severity |
|---|---|---|
| DOCUMENTS_MISSING | The disbursement request, credit agreement, purchase contract or invoice is missing from the checklist | Error (blocks) |
| CONTRACT_EXPIRED | The credit agreement's last valid date is before the check date | Error (blocks) |
| LIMIT_SNAPSHOT_STALE | The limit snapshot date is before the check date | Warning (review needed) |
| LIMIT_SNAPSHOT_FUTURE | The limit snapshot date is after the check date | Error (blocks) |
| LIMIT_EXCEEDED | The request exceeds max(0, limit − outstanding balance) | Error (blocks) |
| INVOICES_MISSING | There are no invoice data rows | Error (blocks) |
| DUPLICATE_INVOICE | The same seller tax ID (MST) and invoice number appear more than once in the same case | Error (blocks) |
| BENEFICIARY_MISMATCH | The seller's tax ID differs from the beneficiary's tax ID | Error (blocks) |
| BORROWER_MISMATCH | The buyer's tax ID differs from the borrower's tax ID | Error (blocks) |
| INVOICE_FUTURE | The invoice date is after the check date | Error (blocks) |
| INVOICE_BALANCE_EXCEEDED | The request exceeds the total remaining value of the invoices that passed validation | Error (blocks) |

Invoices with the wrong buyer or seller, dated in the future, or duplicated are not counted toward
the remaining value. Each invoice's remaining value = invoice value − amount already financed.
A financed amount greater than the invoice, negative numbers, NaN, infinity, fractional VND amounts,
unknown fields and foreign currencies are all rejected with HTTP 422. Limits: 100 invoices per case,
200 characters per text field, and 15 digits for each input monetary value and for the total invoice
value, to preserve precision when displayed on the frontend.

The check date is taken from the server in the `Asia/Ho_Chi_Minh` time zone; a credit agreement is
still valid on its expiry date. Money is compared exactly using Decimal; a value equal to the
threshold is accepted. No findings = `Ready`; warnings only = `Review required`; any error = `Blocked`.

## API and data

- `POST /api/v1/banking/analyze`, requires the existing session/API key, minimum VIEWER.
- Schema: `src/preflight/banking.py`; TypeScript: `apps/web/app/lib/types.ts`.
- Money is sent in JSON as strings; the frontend converts to numbers only for display.
- `findings[].fields` indicates only where the data is located; `evidence` holds the cross-check values
  and the document source supplied by the person entering the data. This is not evidence verified by OCR.
- The downloaded result contains the case, the result, the check date and the rule version;
  it is not an audit certificate and carries no digital signature.

## Limitations and next steps

`Ready` only confirms that the supplied data passed the sample set of checks. It does not check the
authenticity of the documents, the beneficiary account number, detailed disbursement conditions,
KYC/AML, collateral, limit reservations, or financing in other cases or at other banks.
Duplicate checking is performed only within the current payload.

To deploy a pilot with real case storage and processing, the following must be agreed with the bank:

1. Loan products, checklist, data sources, and a versioned exception policy.
2. Multi-document cases; approved OCR and the location of the original evidence.
3. Storage segregated by organizational unit, version history and per-case access control.
4. An independent preparer and approver, including for admins; approval tied to the case version.
5. Independently retained audit, SSO/MFA and the bank's own deployment controls.
6. Read limit data first; reconciliation/idempotency before writing to the target system.

Measure check time, missed-error rate, false-alarm rate and the number of document resubmission
rounds on a set of cases labeled by business officers.

## Testing

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_banking*.py'
./scripts/test.sh
# From apps/web: UI interaction tests against a mocked API, desktop and mobile.
npx playwright test --config playwright.banking.config.ts
```
