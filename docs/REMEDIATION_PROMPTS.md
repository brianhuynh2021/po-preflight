# PO PREFLIGHT REMEDIATION PROMPT SET — FROM DEMO TO A PRODUCT READY TO SELL

> Version 1.0 · 2026-09-02 · Applies to branch `dev` @ `9103e7a`
> Source: review report "PO Preflight Review" (8 reproduced bugs + ~20 findings from reading the code)

---

## PART 0 — HOW TO USE THIS PROMPT SET

### 0.1. Operating principles

1. **One prompt = one session = one branch = one PR.** Do not combine them. The branch name is given in each prompt.
2. **Always paste `PROMPT 00 (Shared context)` at the top** of every session, before the specific prompt. Prompt 00 contains the project's invariant rules; later prompts only reference them and do not repeat them.
3. **Mandatory order:** A1 → A2 → A3 → A4 → A5 → … Prompts within the same phase depend on one another; the dependency table is in section 0.3.
4. **Definition of Done for every prompt** (the agent must self-check before reporting completion):
   - `PYTHONPATH=src python -m unittest discover -s tests` → 0 failures.
   - `cd apps/web && npx tsc --noEmit && npm run lint` → 0 errors.
   - New tests go through **HTTP** (`starlette.testclient`) for every route change; not only tests of pure functions.
   - No new `except Exception: pass`. No new silent fallback.
   - Commit following Conventional Commits, described in English, with the commit body listing the main files.
5. **When the agent finds a conflict** between the prompt and the current code → stop and report back with file:line; do not invent a different direction on its own.

### 0.2. How to paste a prompt

```
[Paste PROMPT 00 — Shared context]

---

[Paste PROMPT A1 …]
```

### 0.3. Dependency table

| Prompt | Depends on | Estimate |
|---|---|---|
| A1 RuleContext | — | 0.5 day |
| A2 DecisionService | A1 | 1 day |
| A3 ERP payload | — | 0.5 day |
| A4 Error taxonomy | — | 0.5 day |
| A5 Remove silent fallback | A3, A4 | 1 day |
| A6 Catalog schema | A1 | 0.5 day |
| A7 FE auth + real UI | A2, A4, A5 | 2 days |
| A8 Landing & claims | — | 0.5 day |
| A9 Config/CI/Deploy | A5 | 0.5 day |
| B1 Data model v2 + migration | A-all | 3 days |
| B2 Line item v2 (VAT/discount/UOM) | B1 | 2 days |
| B3 Rules v2 | B2 | 2 days |
| B4 Revision & duplicate | B1 | 1.5 days |
| B5 Customer master | B1 | 1.5 days |
| B6 Users/roles/approval matrix | B1, A2 | 2 days |
| B7 Inventory source & ATP | B1, B2 | 2 days |
| B8 Observability | A4 | 1 day |
| C1 Email intake | B-all | 2 days |
| C2 Job queue & Redis | B-all | 2 days |
| C3 Real MISA connector | A3, B2 | 3 days + sandbox |
| C4 Real Zalo OA | A2, B6 | 2 days |
| C5 Real embeddings & eval | B5 | 2 days |
| C6 FE pilot-ready | A7, B-all | 3 days |
| C7 Pilot metrics | B8 | 1 day |
| C8 Honest marketing | C7 | 1 day |

---

## PROMPT 00 — SHARED CONTEXT (PASTE AT THE START OF EVERY SESSION)

```
You are working on the PO Preflight repo (github.com/brianhuynh2021/po-preflight, branch dev).

## What the project is
A pre-check gateway for B2B purchase orders (POs) for Vietnamese distributors: it receives PO files
(JSON/CSV/TXT/PDF/Excel/images), extracts their contents, matches SKUs, runs deterministic rules
(price, stock, duplicates, credit/receivables, UOM), has an authorized person approve
(Web/Telegram/Zalo), and only then pushes into the ERP via a Transactional Outbox.

## Stack
- Backend: Python 3.11+, FastAPI, Pydantic v2, SQLite (dev) / PostgreSQL (prod), LangGraph, RapidFuzz.
  Source code at src/preflight/. Tests: tests/*.py using unittest + starlette.testclient.
  Run tests: PYTHONPATH=src python -m unittest discover -s tests
- Frontend: Next.js 16 (via vinext/Vite), React 19, TypeScript strict, CSS custom properties in
  apps/web/app/globals.css (M3 tokens). API client SDK: apps/web/app/lib/api/client.ts.
  Domain types: apps/web/app/lib/types.ts, derived logic: apps/web/app/lib/derive.ts.
  Run checks: cd apps/web && npx tsc --noEmit && npm run lint
- Module architecture: parsers.py → rules.py (pure functions) → store.py (BaseAuditStore ABC) →
  api/routes/*.py; agent/ (LangGraph), rag/ (4-tier SKU matcher), erp/ (outbox + adapters),
  bot/ (telegram, zalo), security/ (rbac, rate_limiter, audit_chain), ingestion/ (OCR, excel).

## INVARIANT RULES (violation = PR rejected)
1. NO silent fallback. Every branch that diverts to mock/dry-run/offline must:
   (a) be enabled only by an explicit flag (environment variable or test parameter),
   (b) leave a trace the user can see: a `mode` field in the API response
       (values: "live" | "dry_run" | "mock" | "offline") and a badge in the UI,
   (c) write a WARNING log with the root reason.
   In production (PREFLIGHT_ENV=production) every fallback is forbidden → fail fast.
2. NO `except Exception: pass`. Catch specific exceptions; if you must catch broadly, log
   `logger.exception(...)` and return a coded error.
3. Every decision (approve/reject/needs_changes) from EVERY channel goes through exactly one function
   `preflight.services.decisions.decide_order(...)`. No channel calls store.record_decision directly.
4. The actor of every action is taken from the server-side authenticated principal, never from the payload.
5. The rule engine (rules.py) must be a pure function: no I/O, no network, no env reads. All input
   data goes through RuleContext.
6. Every route change must have a test that goes through HTTP (TestClient), not only a function test.
7. The customer-facing UI uses ONE language: Vietnamese. No GitHub issue numbers, technical variable
   names, or hardcoded figures in the UI. A figure not available from the API → display "—" with a
   reason; never make it up.
8. Do not add marketing claims (100%, Zero-Hallucination, SOX, SOC2…) to code/README/UI.
9. Money: the backend uses Decimal; the FE uses number but always formats via money(value, currency),
   and never hardcodes "$" or "đ" (the Vietnamese dong symbol).
10. Migration: every DB schema change goes through a migration file in src/preflight/migrations/,
    do not edit the SCHEMA string directly (once B1 is complete).

## How to work
- Read the relevant files carefully before editing. Cite file:line when reporting.
- Write the test first for new behavior, run it to see it fail, then fix.
- When done: run all 3 check commands above, list the changed files, describe how to verify manually.
- If the prompt conflicts with the current code or lacks information: STOP and ask, citing file:line.
```

---

# PHASE A — P0: MAKE WHAT ALREADY EXISTS ACTUALLY WORK

Phase goal: after A9, every feature present in the UI/API **either works for real or says plainly that it does not**. No new business functionality.

---

## PROMPT A1 — RuleContext: wire master data and policy into the rule engine

**Branch:** `fix/a1-rule-context`

```
## Objective
The B2B rules (contract price, credit/receivables, UOM/MOQ) and the price tolerance policy are currently NEVER
applied when analyzing an order via the API or the agent, even though rules.py already supports them. Fix this by creating a single
RuleContext object, built in one place, and passing it into analyze_order at all 3 call sites.

## Evidence
- src/preflight/api/routes/orders.py:236   analyze_order(order, catalog, duplicate=duplicate)
- src/preflight/api/routes/orders.py:300   analyze_order(updated_order, catalog, duplicate=False)
- src/preflight/agent/nodes.py:120         analyze_order(order, catalog, duplicate=duplicate)
- src/preflight/api/routes/rules.py:13     _POLICY_STATE is in-memory, nobody reads it apart from GET/PUT
- Reproduction: set /customers/{id}/credit status=BLOCKED → upload PO → ready_for_approval, 0 findings.

## Requirements
1. Create src/preflight/rules_context.py:
   ```python
   @dataclass(frozen=True)
   class RuleContext:
       catalog: dict[str, Product]
       pricing_agreements: tuple[CustomerPriceAgreement, ...] = ()
       uom_conversions: tuple[UOMConversion, ...] = ()
       customer_credit: CustomerCreditProfile | None = None
       price_tolerance_percent: Decimal = Decimal("0")
       stock_safety_margin: int = 0
       allow_inactive_sku: bool = False
       duplicate: bool = False
       fx_rates: Mapping[str, Decimal] = field(default_factory=dict)  # "USD_VND" -> rate

   def build_rule_context(store: BaseAuditStore, catalog, order: Order, *, policy: RulePolicy,
                          fx_provider: Callable[[str, str], Decimal] | None = None) -> RuleContext:
       ...
   ```
   - build_rule_context is the ONLY PLACE that calls store.get_customer_pricing / get_uom_conversions /
     get_customer_credit / has_po, and that calls fx_provider for the currency pairs appearing in the order.
   - Customer lookup: for now keep using the name string as it is today, but normalize it through a function
     `normalize_customer_key(name)` (strip, upper, remove diacritics, remove the prefixes "CÔNG TY" (company),
     "CTY" (company, abbreviated), "CÔNG TY CỔ PHẦN" (joint-stock company), "CT CP" (joint-stock company, abbreviated),
     "TNHH" (limited liability), "MTV" (single-member), and periods/commas). State clearly with TODO(B5) that it will be
     replaced by customer_id.
2. Change the signature:
   `analyze_order(order: Order, ctx: RuleContext) -> Analysis`
   Keep the old function under the name `analyze_order_legacy(...)` calling into the new one, marked deprecated, so that
   old tests do not break immediately; delete it at the end of the prompt after all tests have been updated.
3. rules.py must become a pure function: remove `from preflight.currency import fx_engine`; use
   ctx.fx_rates. If the exchange rate for a currency pair is missing → add Finding code="FX_RATE_UNAVAILABLE"
   severity="error" (do not guess exchange rates).
4. Policy: create a Pydantic model RulePolicy (price_tolerance_percent: Decimal, stock_safety_margin: int,
   allow_inactive_sku: bool, auto_approve_ready: bool). Persist it to a new table `rule_policies`
   (id=1 singleton, json, updated_at, updated_by). Add store.get_policy()/set_policy() to
   BaseAuditStore, for both SQLite and Postgres. routes/rules.py reads/writes through the store; delete _POLICY_STATE.
   (Temporarily edit the SCHEMA string directly because the migration runner does not exist yet — note TODO(B1).)
5. Apply stock_safety_margin: INSUFFICIENT_STOCK when base_quantity > stock - safety_margin.
   Apply allow_inactive_sku: if True, INACTIVE_SKU is downgraded from error to warning.
6. Update the 3 call sites (orders.py x2, nodes.py) to use build_rule_context + the new analyze_order.
   Upload, confirm-extraction and the agent must all produce the same result for the same input.
7. currency.py: keep DynamicFXEngine but it may only be called from build_rule_context via fx_provider;
   add the flag PREFLIGHT_FX_LIVE (default false). When false → use only FALLBACK_RATES and mark
   ctx.fx_rates with source "static". Record the exchange-rate source in the PRICE_MISMATCH message.

## Do not
- Do not change the text of existing finding messages other than the exchange-rate source part (the FE maps by code).
- Do not rename or add finding codes other than FX_RATE_UNAVAILABLE.

## Acceptance criteria (write tests first)
tests/test_rule_context_http.py, going through TestClient with a temporary DB and dependency_overrides:
  a) set credit BLOCKED → upload → status "blocked", has CUSTOMER_BLOCKED.
  b) set contract price 17,000,000 for LAPTOP-A14 → upload at price 17,000,000 → no PRICE_MISMATCH.
  c) PUT /rules tolerance=10 → upload deviating by 2.7% → no PRICE_MISMATCH; tolerance=0 → has PRICE_MISMATCH.
  d) set uom CARTON=20 PCS for CAB-CAT6-3M → upload qty 2 CARTON → compare stock against 40 PCS.
  e) restart the store (close/reopen) → policy is still there (persisted).
  f) POST /agent/run with the same data as (a) → risk_level HIGH, finding CUSTOMER_BLOCKED.
  g) USD order when PREFLIGHT_FX_LIVE=false → PRICE_MISMATCH message contains "tỷ giá tĩnh" (static exchange rate).
Old tests: update to the new signature; delete analyze_order_legacy once nobody calls it.

## Deliverables
- Files: rules_context.py (new), rules.py, routes/orders.py, routes/rules.py, agent/nodes.py,
  store.py (policy), currency.py, new tests.
- Commit: "fix(rules): introduce RuleContext and wire B2B master data, policy and FX into all analyze paths"
```

---

## PROMPT A2 — DecisionService: a single entry point for every decision, actor from auth

**Branch:** `fix/a2-decision-service`

```
## Objective
There are currently 3 different paths that write decisions: the /decide route (has governance), the Telegram webhook and the Zalo
webhook (call store.record_decision directly, NO governance, NO auth), and the agent's human_approval_node
(only changes state). Reproduced consequence: a Blocked order was approved via Telegram by a self-declared payload.
In addition, the actor in /decide is sent by the client (reproduced "CEO_Nguyen_Van_A").

## Evidence
- src/preflight/bot/telegram.py:220-245   record_decision called directly
- src/preflight/bot/zalo.py:196-203        record_decision called directly
- src/preflight/api/routes/orders.py:317   payload.actor is used as the actor
- src/preflight/api/schemas.py:161         DecisionRequest.actor: str
- src/preflight/api/routes/bot.py:77-95    webhook does not require a secret in dev

## Requirements
1. Create src/preflight/services/__init__.py and src/preflight/services/decisions.py:
   ```python
   @dataclass(frozen=True)
   class Principal:
       user_id: str; display_name: str; role: Role; channel: Literal["web","telegram","zalo","api","agent"]

   @dataclass(frozen=True)
   class DecisionResult:
       decision_id: int; po_number: str; decision: str; actor: str; note: str; created_at: str
       previous_status: str; new_status: str

   class DecisionError(Exception):  # carries status_code + code + message
       ...

   def decide_order(store: BaseAuditStore, *, order_ref: str | int, decision: str, note: str,
                    principal: Principal, event_bus: EventBus | None = None) -> DecisionResult:
       # 1. load order (404 if it does not exist)
       # 2. RBAC: principal.role >= MANAGER (403)
       # 3. validate_order_decision(current_status, decision, note, error_count) (409/422)
       # 4. store.record_decision(po, decision, actor=f"{principal.channel}:{principal.user_id}",
       #                          note, display_name=principal.display_name)
       # 5. publish "order.decided" with actor, channel
       # 6. return DecisionResult
   ```
2. routes/orders.py /decide: remove actor from DecisionRequest (keep compatibility: if the client sends
   actor → ignore it and return the header `X-Deprecated-Field: actor`). The Principal is built from UserPrincipal
   (rbac.get_current_user), channel="web" if the header X-Client: web is present, else "api".
3. Telegram:
   - Create the table `channel_identities(channel, external_id, user_id, display_name, role, created_at)`
     UNIQUE(channel, external_id). Add store.get_channel_identity()/upsert_channel_identity().
   - handle_callback_action receives from_user.id (not the username) and looks it up in channel_identities;
     if not found → return the popup "Tài khoản Telegram chưa được liên kết. Liên hệ quản trị." (Telegram account not
     linked yet. Contact an administrator.) and write NOTHING.
   - If found → call decide_order. On DecisionError → the corresponding Vietnamese popup message
     (409 blocked: "Đơn đang bị chặn, không thể duyệt." (The order is blocked and cannot be approved.);
     422: "Cần ghi chú ≥10 ký tự — hãy duyệt trên web." (A note of at least 10 characters is required — please approve on the web.)).
   - After a successful decision: call editMessageReplyMarkup to disable the buttons (prevents double-clicking).
   - Webhook: TELEGRAM_WEBHOOK_SECRET is REQUIRED in every environment; missing → 503 even in dev.
   - Admin endpoint: POST /api/v1/bot/telegram/link {telegram_user_id, user_id, role} (ADMIN).
4. Zalo: similar — process_webhook_event takes sender.id, looks it up in channel_identities, calls decide_order.
   verify_webhook_signature: when there is no secret_key → return False (no more "dev mode True").
5. Agent human_approval_node: receives state["decision"], state["decided_by"] (an internal user_id),
   calls decide_order with channel="agent"; on DecisionError → set state["status"]="decision_rejected",
   state["error"]=message, do NOT proceed to erp_sync. Update route_after_human_approval.
6. Remove every other place that calls store.record_decision outside services/decisions.py. Add a static test:
   grep in src/ finds no "record_decision(" outside store.py and services/decisions.py.
7. record_decision in the store: add the columns `display_name`, `channel` to decisions (edit SCHEMA,
   TODO(B1)); the audit block payload also includes channel.

## Acceptance criteria
tests/test_decision_service_http.py:
  a) POST /decide with a body containing "actor":"X" → the response actor is the API key's username, not X.
  b) Telegram webhook approves a blocked order (MANAGER identity already linked) → 200 but result.success=False,
     the popup contains "bị chặn" (blocked); the order remains blocked.
  c) Telegram webhook from an unlinked user → no decision written; popup "chưa được liên kết" (not linked yet).
  d) Telegram webhook missing the secret header → 403; server missing TELEGRAM_WEBHOOK_SECRET → 503 even in dev.
  e) Zalo webhook without a signature → 401; with a correct signature + VIEWER identity → 403 (insufficient role).
  f) Agent resume with decision APPROVED on a blocked order → status decision_rejected, erp_synced False.
  g) A second approve on the same order → 409.
  h) grep test: no record_decision left outside the 2 permitted files.

## Deliverables
- Commit: "fix(security): route all channel decisions through DecisionService with authenticated actor and governance"
```

---

## PROMPT A3 — ERP payload with correct data, adapter chosen by configuration, no faked success

**Branch:** `fix/a3-erp-payload`

```
## Objective
The outbox currently receives items=[] (the ERP route reads the wrong key) and the agent sends items=[] total=0 (it reads keys
that do not exist in the state). The live adapter returns success=True in dry-run without distinguishing it. Fix this so that the
ERP payload is always a complete copy of the approved order and the run mode is always visible.

## Evidence
- src/preflight/api/routes/erp.py:48-50    order.get("line_items") or order.get("items", []) — the row only has order_json
- src/preflight/agent/nodes.py:232-238     state.get("items"), state.get("total"), state.get("currency") — not in PreflightAgentState
- src/preflight/erp/adapters/odoo_live.py:31  dry_run → success=True with no trace
- Reproduction: outbox payload items: [] total_amount: 18000000.0 (API) / 0.0 (agent)

## Requirements
1. Create src/preflight/erp/payload.py:
   ```python
   def build_erp_payload(order_row: dict[str, Any] | Order, *, decision: DecisionResult | None) -> ERPOrderDraft
   ```
   - Accepts a row from the store (parse order_json) OR a domain Order; returns a dataclass containing po_number, customer,
     currency, items (sku, description, quantity, uom, unit_price, line_total), subtotal, approved_by,
     approved_at, source_analysis_id. Raise ValueError if items is empty or the total ≠ Σ line_total.
2. routes/erp.py /sync/{order_id}: only allowed when order.latest_decision == "approved" (409 otherwise).
   Use build_erp_payload. Remove the branch "If already sent previously, return idempotent success" that
   invents the transaction_id "ERP-SO-{po}"; replace it by re-reading the outbox by idempotency_key and returning the real record.
3. agent/nodes.py erp_sync_node: use state["order"] (already present from audit_rules_node) via build_erp_payload;
   remove every state.get("items"/"total"/"currency").
4. Idempotency key: currently = sha256(po:customer:total)[:24]. Change it to sha256(analysis_id:po:revision_hash)
   where revision_hash = the sha256 of the normalized items. Reason: the same PO with the same total but different lines must
   be a different event.
5. Adapter selection: create erp/registry.py with get_adapter(name: str | None) reading ERP_DEFAULT_ADAPTER
   (MOCK_SAP|MOCK_ODOO|ODOO_LIVE|SAP_LIVE|MISA_AMIS_LIVE). The route accepts an optional adapter_type but
   only ADMIN may override it. The agent uses get_adapter(None).
6. ERPSyncResponse adds the field `mode: Literal["live","dry_run","mock"]`. Every adapter sets mode correctly.
   A live adapter missing credentials:
   - PREFLIGHT_ENV=production → raise ERPConfigurationError → outbox mark_failed with the reason,
     NOT success.
   - dev → mode="dry_run", transaction_id with the prefix "DRYRUN-", log WARNING.
7. Outbox: add a real PROCESSING status (fetch_pending marks PROCESSING in the same transaction,
   preventing 2 workers from processing the same item twice); retry backoff (retry_count → delay 1m/5m/30m, column next_attempt_at);
   after 3 attempts → DEAD_LETTER (a new status), not mixed with FAILED.
8. The worker records metrics_registry.record_erp_sync(adapter, success) (the function exists now but nobody calls it).

## Acceptance criteria
tests/test_erp_payload_http.py:
  a) upload a 3-line PO → approve (via /decide with a valid note) → /erp/sync → the outbox payload_json
     has exactly 3 items, subtotal = the order total, correct currency.
  b) /erp/sync on an unapproved order → 409.
  c) Agent run on a clean order (LOW) → erp_synced True and the outbox items match the input line_items.
  d) Sync twice for the same order → 1 event in the outbox, the 2nd call returns the old record (same mode, transaction_id).
  e) ODOO_LIVE without credentials + PREFLIGHT_ENV=production → event FAILED, response success=False,
     error_message contains "credential".
  f) dev → mode="dry_run", transaction_id starts with "DRYRUN-".
  g) mark_failed 3 times → status DEAD_LETTER; fetch_pending no longer returns it.

## Deliverables
- Commit: "fix(erp): build full ERP payload from persisted order, honest sync modes, outbox processing/dead-letter"
```

---

## PROMPT A4 — Error taxonomy: coded errors, not swallowed, no internal leakage

**Branch:** `fix/a4-error-taxonomy`

```
## Objective
The upload route wraps `except Exception` → every error (413, 404, NameError, IntegrityError) becomes
400 "Failed to process PO file: <str(exc)>". `status` is not imported, causing a NameError when the file is >10MB.
Standardize all API errors per RFC 7807 Problem Details, with machine-readable codes so the FE can display them correctly.

## Evidence
- src/preflight/api/routes/orders.py:200   status.HTTP_413_… but status is not imported
- src/preflight/api/routes/orders.py:246-248  except Exception → 400 + str(exc)
- Reproduction: upload 11MB → 400 "name 'status' is not defined"

## Requirements
1. Create src/preflight/api/errors.py:
   ```python
   class PreflightError(Exception):
       status_code: int; code: str; message_vi: str; detail: dict | None
   # Subclasses: ParseError(400,"PARSE_ERROR"), UnsupportedFormat(415,"UNSUPPORTED_FORMAT"),
   #      PayloadTooLarge(413,"PAYLOAD_TOO_LARGE"), NotFound(404,"NOT_FOUND"),
   #      DecisionConflict(409,"DECISION_CONFLICT"), ValidationFailed(422,"VALIDATION_FAILED"),
   #      Forbidden(403,"FORBIDDEN"), Unauthorized(401,"UNAUTHORIZED"),
   #      UpstreamUnavailable(503,"UPSTREAM_UNAVAILABLE"), ConfigurationError(500,"CONFIGURATION_ERROR")
   ```
   An exception handler registered on the app returns JSON:
   {"type":"https://popreflight.vn/errors/<code>","title":..., "status":..., "code":..., "detail": message_vi,
    "request_id": <X-Request-ID>, "errors": [...] (optional)}
   Content-Type: application/problem+json.
2. A handler for RequestValidationError (Pydantic) → 422 code "VALIDATION_FAILED", errors = a list of
   {field, message} translated into basic Vietnamese (required, type, min_length).
3. A handler for unforeseen Exception → 500 code "INTERNAL_ERROR", fixed detail
   "Lỗi hệ thống. Mã tham chiếu: {request_id}" (System error. Reference code: {request_id}). logger.exception with the request_id.
   NEVER return str(exc).
4. routes/orders.py upload: import status; split the try: it wraps only parse_order → ParseError; check the size
   before writing the file; HTTPException/PreflightError are not caught again. Delete the temp file when parsing fails.
   Write the uploaded file as <analysis_id>/<safe_name> after the id exists (currently a random name that cannot be traced back).
   Store the path in the column analyses.source_path (SCHEMA, TODO(B1)).
5. All other routes: replace HTTPException(detail=str) with the corresponding PreflightError; keep the old HTTP codes.
6. rbac.py: 401/403 via Unauthorized/Forbidden to unify the format.
7. Rate limiter: 429 also follows the problem+json format, code "RATE_LIMITED", with Retry-After.
8. FE SDK (client.ts): ApiError parses problem+json → has .code, .requestId, .detailVi; export a
   function `describeError(err): string` that returns Vietnamese. (The UI uses it in A7.)

## Acceptance criteria
tests/test_error_taxonomy.py:
  a) upload 11MB → 413, body.code == "PAYLOAD_TOO_LARGE", has request_id, does not contain "NameError".
  b) upload .docx → 415 UNSUPPORTED_FORMAT.
  c) upload JSON missing po_number → 400 PARSE_ERROR, Vietnamese detail, does not contain a traceback.
  d) GET /orders/999999 → 404 NOT_FOUND in problem+json format.
  e) decide missing note → 422 VALIDATION_FAILED or DECISION_CONFLICT, whichever fits the context.
  f) simulate an internal error (monkeypatch store.get_order to raise RuntimeError("secret-db-path")) →
     500 INTERNAL_ERROR, the body does NOT contain "secret-db-path".
  g) No junk files remain in runtime/uploads after a failed upload.

## Deliverables
- Commit: "fix(api): RFC7807 problem details, typed errors, no exception leakage, upload size guard"
```

---

## PROMPT A5 — Remove every silent fallback

**Branch:** `fix/a5-no-silent-fallback`

```
## Objective
The system currently looks "green" at every layer even though nothing actually runs: Postgres→SQLite, Gemini→fabricated order,
Telegram/Zalo→success=True, ERP→dry-run success, FE→seed data. Make each place either run for real,
or fail clearly, or carry a mode label.

## Evidence
- src/preflight/store.py:825-838            Postgres error → AuditStore("runtime/pg_fallback.db")
- src/preflight/erp/outbox.py:283-297       same
- src/preflight/ingestion/ocr_engine.py:64-71, 150-194   the mock returns the order "Northstar Scanned Ingestion" conf 0.92
- src/preflight/ingestion/pipeline.py:41,92 except Exception: pass
- src/preflight/bot/telegram.py:127-137     dry-run success=True message_id "mock_msg_12345"
- pyproject.toml has no psycopg; the Dockerfile does not install it → Postgres has never run in a container

## Requirements
1. Postgres:
   - Add the dependency `psycopg[binary,pool]>=3.1` (psycopg 3, not psycopg2) to pyproject
     [project.dependencies]. Update PostgresAuditStore/PostgresOutboxStore to the psycopg3
     ConnectionPool. Remove _fallback_sqlite entirely. A connection error → raise ConfigurationError
     at startup (lifespan) → the process exits with a clear log.
   - /health/ready returns 503 if the DB cannot be queried; the body states the real backend ("postgresql"/"sqlite")
     instead of hardcoding "sqlite" (routes/health.py:52).
   - tests/test_database_dual_backend.py: the Postgres part runs only when the TEST_DATABASE_URL variable is set,
     otherwise skipTest with a clear reason — it must not pass falsely on the fallback.
2. OCR:
   - GeminiVisionOCREngine.extract: missing api_key → raise UpstreamUnavailable("OCR chưa cấu hình") (OCR not configured).
     A Gemini call error → raise UpstreamUnavailable with the reason, going through vision_ai_circuit_breaker
     (it exists but is unused — resilience/circuit_breaker.py).
   - The mock extractor moves to tests/fixtures/mock_ocr.py, injected only via the engine parameter in tests.
     Remove _mock_vision_extraction from src.
   - Pipeline: remove the 2 `except Exception: pass`; Excel errors → raise ParseError with the sheet/row if available;
     a text parser error → try OCR ONLY when doc_type is SCANNED_PDF/IMAGE_RASTER, not for broken JSON/CSV.
     ExtractedOrder adds a `mode` field and `extractor_used` already exists → make sure they are truthful.
   - Route /ingest/extract: when OCR is unavailable → 503 UPSTREAM_UNAVAILABLE with the guidance
     "Tải lên Excel/CSV hoặc nhập tay tại Staging" (Upload Excel/CSV or enter manually at Staging).
3. Bot:
   - BotNotificationResult adds `mode`. Missing token → mode="dry_run", success=True ONLY when
     TELEGRAM_DRY_RUN=true is set explicitly; otherwise → success=False, details "Telegram chưa cấu hình" (Telegram not configured).
     Production + not configured → do not send, write an audit block "NOTIFY_SKIPPED".
   - The fake message_id "mock_msg_12345"/"zalo_msg_simulated_9988" → None on dry-run.
4. ERP: handled in A3; re-check that every adapter sets mode.
5. LangGraph checkpointer: MemorySaver → if DATABASE_URL is postgres use langgraph-checkpoint-postgres,
   if sqlite use langgraph-checkpoint-sqlite (file runtime/agent_checkpoints.db). Add the dependencies.
   No more in-memory _SERVER_CHECKPOINTER.
6. Add the endpoint GET /api/v1/system/modes (VIEWER) returning:
   {"database":"postgresql|sqlite","ocr":"live|unavailable","telegram":"live|dry_run|unconfigured",
    "zalo":..., "erp":{"adapter":"...", "mode":"live|dry_run|mock"}, "fx":"live|static",
    "environment": PREFLIGHT_ENV, "auth_required": bool}
   The FE will use it to display a banner (A7). /metrics: remove the hardcoded version/environment; read them from
   preflight.__version__ and PREFLIGHT_ENV.
7. Dockerfile: install `.[pdf]` and psycopg; pin Python 3.12 (matching CI); the healthcheck uses /health/ready.
   docker-compose: add a postgres service (postgres:16), with the backend DATABASE_URL pointing to it; a
   `sqlite` profile for lightweight dev.

## Acceptance criteria
  a) DATABASE_URL=postgresql://invalid → app startup raises, and runtime/pg_fallback.db is not created.
  b) /ingest/extract on a PNG image without GEMINI_API_KEY → 503 UPSTREAM_UNAVAILABLE; there is no
     "Northstar Scanned Ingestion" record in the DB. grep src/ no longer finds "Northstar Scanned".
  c) telegram/notify with no token and no TELEGRAM_DRY_RUN → success=False mode="unconfigured".
  d) GET /system/modes reflects the env correctly in the test (set different envs via monkeypatch).
  e) /agent/run and then creating a new graph (simulating a restart) → /agent/state/{thread} can still be found.
  f) grep src/ no longer finds "except Exception:\n *pass".
  g) docker compose up (sqlite profile) → /health/ready 200; (postgres profile) → database=postgresql.

## Deliverables
- Commit: "fix(core): remove silent fallbacks (db, ocr, bots, checkpointer); expose system modes; real Postgres support"
```

---

## PROMPT A6 — Complete catalog schema: moq, pack_size, base_uom; the parser keeps UOM

**Branch:** `fix/a6-catalog-schema`

```
## Objective
The MOQ/pack/UOM rules live only in unit tests because load_catalog reads only 5 columns and the parser drops the uom of line items.

## Evidence
- src/preflight/catalog.py:13-20      only sku,name,unit_price,stock,active
- src/preflight/parsers.py:42-47      LineItem does not accept uom
- examples/catalog.csv                has no such columns
- Reproduction: get_catalog()["LAPTOP-A14"].moq == 1 (default)

## Requirements
1. catalog.py: also read the optional columns `base_uom` (default PCS), `moq` (int ≥1), `pack_size` (int ≥1),
   `category`, `barcode`. Missing column → default; wrongly typed value → raise ValueError with the line number.
   The catalog path is read from env CATALOG_PATH (deps.py currently hardcodes it). Cache the catalog by file mtime
   (it currently parses the CSV on every request).
2. Product adds `category: str | None`, `barcode: str | None`.
3. parsers.py: JSON/CSV/TXT accept `uom` (default PCS); the TXT format allows 4 columns
   `SKU | QTY | UOM | UNIT_PRICE` and still accepts the old 3 columns. The Excel extractor already reads uom → keep it.
4. examples/catalog.csv: add the columns with reasonable data; add examples/orders/po-carton.json that uses
   uom CARTON, which requires a conversion.
5. API /catalog: return the new columns. Add POST /api/v1/catalog/import (ADMIN, multipart CSV): validate
   everything first, report errors per row (422 VALIDATION_FAILED, errors=[{row, column, message}]),
   on success write the new file + keep the old one with a timestamp (no silent overwrite — PRD FR-054),
   and write an audit block "CATALOG_IMPORTED".
6. Catalog UI (apps/web/components/catalog/CatalogView.tsx): display base_uom, MOQ, pack size;
   the button "Nhập catalog CSV" (Import catalog CSV) calls the new endpoint and displays errors per row.
7. FE types: Product adds baseUom, moq, packSize.

## Acceptance criteria
  a) new catalog → moq/pack correct; the old 5-column catalog can still be loaded.
  b) upload po-carton.json + uom conversion → INSUFFICIENT_STOCK is computed in PCS; no conversion →
     finding UOM_CONVERSION_MISSING (warning, add this new code, update the FE FINDING_TITLE).
  c) qty 3 with pack_size 5 → INVALID_PACK_SIZE via HTTP.
  d) import a CSV with an error row → 422 with row/column; the old file is unchanged.
  e) edit the catalog file on disk → the next request sees the new data (cache by mtime).

## Deliverables
- Commit: "feat(catalog): full product schema (uom/moq/pack), CSV import with validation, parsers keep UOM"
```

---

## PROMPT A7 — Frontend: real login, real data, one language, complete decisions

**Branch:** `fix/a7-frontend-truth`

```
## Objective
The FE currently sends no authentication (every POST gets 401), catches errors and fakes success, is full of hardcoded figures,
mixes English and Vietnamese, lacks a Reject button, accepts notes shorter than 10 characters, shows "$" for VND orders, and has headings containing issue numbers.

## Evidence
- apps/web/app/lib/api/client.ts:44-52           no auth header
- apps/web/components/orders/OrdersView.tsx:72-79  catch → local Approved status + toast "was approved"
- OrdersView.tsx:227-247   "Average decision time 6m", "42", hardcoded spark
- OrdersView.tsx:470-478   `$${line.unitPrice.toFixed(2)}`
- overview/OverviewView.tsx:20-60   "GOOD MORNING, MAYA", "Two orders need attention", 86%, +18%
- layout/Sidebar.tsx:85,161  Northwind Co., Maya Chen; :149 hardcoded "Processing is healthy"
- settings/SettingsView.tsx:45  "(ISSUE #8 & #43)"; staging/ExtractionReviewStudio.tsx:33 "(Issue #38)"
- orders/DecisionModal.tsx:59  disabled only when the note is empty (the backend needs ≥10)
- AppStateProvider.tsx: isLiveConnected is computed but not displayed

## Requirements
### 1. Authentication
- Backend: add POST /api/v1/auth/login {api_key} → set an HttpOnly cookie `pf_session` (JWT HS256,
  exp 8h, secret PREFLIGHT_SESSION_SECRET required in production) and return {user, role}.
  GET /api/v1/auth/me, POST /api/v1/auth/logout. rbac.get_current_user accepts the cookie or the header.
  CORS allow_credentials=True with a specific origin (already in place).
- FE: a /login page (outside the app shell), a form for entering an API key (temporary, until B6 provides user/password).
  Next middleware: no cookie → redirect to /login. client.ts: fetch with credentials:"include";
  401 → clear and go to /login.
- Show the real user in the Sidebar (from /auth/me), remove "Maya Chen"/"Northwind Co."; the workspace name
  is read from GET /api/v1/system/modes (add the field company_name from the env PREFLIGHT_COMPANY_NAME).

### 2. No faked success
- Remove every `catch {}` that hides errors in OrdersView, CatalogView, SettingsView. Error → red toast with
  describeError(err) (A4). Success → only after a successful await and refreshOrders().
- Remove seedOrders as the initial state. Before the API responds → skeleton; API error → EmptyState
  "Không kết nối được máy chủ (mã lỗi …)" (Cannot connect to the server (error code …)) + a retry button. seed.ts is then used only for
  Storybook/tests, moved to apps/web/tests/fixtures/.
- Mode banner: read /system/modes; if any entry is dry_run/mock/unavailable → a yellow banner at the
  top of the page "Hệ thống đang chạy chế độ thử: OCR chưa cấu hình, Telegram dry-run…" (The system is running in
  trial mode: OCR not configured, Telegram dry-run…). In production, when there is nothing to report, it is not shown.
- Sidebar "Processing is healthy" → read /health/ready periodically every 30s: "Hệ thống ổn định" (System stable) / "Mất kết nối" (Connection lost).

### 3. Real figures
- OrdersMetrics and Overview: use GET /api/v1/dashboard/stats; add to the backend:
  approved_today, avg_decision_minutes (from decisions.created_at − analyses.created_at),
  orders_last_7_days (an array of 7 numbers), straight_through_rate (ready_for_approval / total).
  No data → "—". Remove 86%, +18%, 42, 6m, the hardcoded sparkline.
- The Overview headline is generated from data: "{n} đơn cần xử lý" ({n} orders need handling) (n=0 → "Không có đơn cần xử lý" (No orders need handling)).
  Remove "GOOD MORNING, MAYA", "2:00 PM cut-off".

### 4. Decisions
- DecisionModal: 3 actions `Duyệt` (Approve) / `Yêu cầu sửa` (Request changes) / `Từ chối` (Reject) in one modal with radio buttons; validateNote
  from derive.ts (MIN_NOTE_LENGTH=10) blocks the button and shows a character counter; display the reason when an action is
  locked (decisionBlockedReason). Remove the line "attributed to Maya Chen" → the real user's name.
- OrdersView: Request changes also opens the modal (it currently sends a hardcoded note that does not go through the user).
- After a decision: the activity/timeline is taken from detail.decisions (already exists), remove the fake initialActivity
  ("Olivia Park").

### 5. Language & copy
- Move the whole chrome to Vietnamese: "Đơn đặt hàng" (Purchase orders), "Cần xử lý" (Needs handling), "Sẵn sàng duyệt" (Ready for approval), "Đã duyệt" (Approved),
  "Tải lên PO" (Upload PO), "Phát hiện kiểm tra" (Check findings), "Dòng hàng chuẩn hóa" (Normalized line items), "Lịch sử" (History), "Yêu cầu sửa" (Request changes), "Xem xét & duyệt" (Review & approve).
  Keep the internal status codes (OrderStatus) but add a STATUS_LABEL_VI map for display; update
  tests/rendered-html.test.mjs and e2e to the new labels.
- Remove every "(Issue #…)" from the H1/eyebrow. Remove the "Marketing Landing Page" link from the sidebar.
- Navigation: 2 groups for operators (`Tổng quan` (Overview), `Đơn hàng` (Orders), Catalog, `Nhật ký` (Audit log), `Cài đặt` (Settings)) and the group
  `Quản trị hệ thống` (System administration) shown only to role ADMIN (`Luật & chính sách` (Rules & policies), ERP Outbox, `Bot & kênh` (Bots & channels), `Công cụ
  kiểm thử SKU` (SKU testing tool), `Sơ đồ quy trình` (Workflow diagram), `Chứng thư nhật ký` (Audit certificate)).

### 6. Currency & numbers
- Every monetary value goes through money(value, order.currency); remove "$…toFixed(2)". VND has no decimals,
  USD has 2 decimals (fix money(): maximumFractionDigits by currency).

### 7. Secondary screens wired to the API
- ERPSyncView: data from api.erp.getOutboxStatus; the button "Chạy đồng bộ" (Run sync) → processOutbox; display
  the mode; the DEAD_LETTER status.
- RulesView: read/write via api.rules (GET/PUT), has a Save button, error feedback.
- ExtractionReviewStudio: a list of orders with status extraction_review from api.orders.list({status}),
  editing lines → api.orders.confirmExtraction; display the returned analysis result.
- AuditView: a new GET /api/v1/audit/events (backend: union of decisions + audit_blocks, paginated,
  filtered by po/actor/action).
- SettingsView: do NOT display tokens; only the configuration status from /bot/status and env guidance;
  remove the fake Save button. Add a section "Liên kết tài khoản Telegram" (Link Telegram account) that calls /bot/telegram/link (ADMIN).
- SideBySideViewer: when order.source_path exists → display the original file (PDF via <iframe> to
  GET /api/v1/orders/{id}/source (stream, VIEWER); images via <img>; JSON/CSV/TXT as <pre>).
  Missing → "Không có tệp gốc" (No original file). Remove "Simulated Document Source".

## Acceptance criteria
- tsc + lint clean. npm test (rendered-html) updated with the Vietnamese labels.
- Playwright (update apps/web/tests/e2e): log in with a manager key → upload examples/orders/po-review.json
  → see 2 real findings from the API → open the approve modal, enter a 5-character note → button locked → 12 characters → approve →
  status "Đã duyệt" (Approved) taken from the refresh (not optimistic) → appears in the "Nhật ký" (Audit log).
- Turn the backend off → the UI shows the error EmptyState, not the seed data.
- grep apps/web/components no longer finds: "Maya", "Northwind", "Olivia", "86%", "+18%", "Issue #", "toFixed(2)".

## Deliverables
- Commit: "feat(web): session auth, real data everywhere, Vietnamese UI, complete decision flow, wire secondary screens"
```

---

## PROMPT A8 — Landing page separated from the app, truthful claims, consistent contact details

**Branch:** `fix/a8-landing-truth`

```
## Objective
The landing page currently renders inside the app shell (with a sidebar), its header is overlapped by a badge, robots indexes the whole app,
claims are unverified, the contact information has 3 different domains/3 different emails, and the lead form sends nothing anywhere.

## Evidence
- apps/web/app/(protected)/landing/page.tsx  lives in the protected route group
- LandingPageView.tsx:102 handleLeadSubmit only does setState; :1415 mailto huynh2102@gmail.com
- app/layout.tsx JSON-LD: personal Facebook, personal email, home address
- docs/PITCH_DECK_VN.md contact@popreflight.com; docs/marketing/ONE_PAGER.md pilot@po-preflight.vn, "09xx-xxx-xxx"
- LandingPageView: "99,4%", "100%", "Zero-Hallucination", "SOX 404", "<15ms", "SAP S/4HANA" logo

## Requirements
1. Move the landing page out to apps/web/app/(marketing)/page.tsx (route "/"), with its own layout with no sidebar and
   no AppStateProvider. The app moves to /app/* (or keep /overview,/orders… but under (protected)
   with the login middleware). robots.ts: allow "/" and "/pricing", disallow "/app", "/orders", "/overview"…
   the sitemap only has marketing pages.
2. Fix the display bug: the badge "Nhật Minh Tech" must not overlap the logo (check at 1280px and 375px, attach
   screenshots to the PR).
3. Claims: replace every unsourced figure with a description of capabilities that can be verified:
   - "99,4% OCR", "100%", "Zero-Hallucination" → "Tự kiểm tra tổng tiền dòng so với tổng đơn; sai lệch
     bị chặn để người kiểm tra." (Automatically checks line totals against the order total; any discrepancy
     is blocked for a person to review.)
   - "SOX 404 / SOC2" → "Nhật ký bất biến có chuỗi băm SHA-256, xuất được để đối soát." (Immutable audit log with a
     SHA-256 hash chain, exportable for reconciliation.)
   - "<15ms", "<30 giây" → "Kiểm tra tự động trong vài giây với file Excel/CSV/PDF có chữ." (Automatic checks within
     seconds for Excel/CSV/text-based PDF files.)
   - "SAP S/4HANA" → the lead row is MISA AMIS, Bravo, Fast, Odoo, SAP Business One (state the status clearly:
     "đang tích hợp" (integration in progress) if no customer is running it for real yet).
   - ROI: turn it into "an estimate for a business with X orders/day" with the formula and assumptions displayed,
     with a button "Tính cho doanh nghiệp bạn" (Calculate for your business) (a simple form, calculated client-side).
4. Contact: one domain (choose popreflight.vn), one company email (env NEXT_PUBLIC_CONTACT_EMAIL),
   one hotline (env). JSON-LD: remove the founder's personal Facebook, remove the home address; keep a minimal
   Organization. Synchronize docs/PITCH_DECK_VN.md, docs/marketing/ONE_PAGER.md, README.
5. Lead form: POST /api/v1/leads (no auth, rate limit 5/minute/IP, honeypot field) → save to the table
   leads (name, company, phone, email, erp, volume, note, created_at, ip_hash) + send an email via
   SMTP if configured (env SMTP_*), otherwise → log + still save to the DB. Return 201, the FE shows "Đã nhận, chúng
   tôi liên hệ trong 1 ngày làm việc" (Received; we will contact you within 1 business day). Add GET /api/v1/leads (ADMIN).
6. Add a /pricing page with 3 skeleton plans (Pilot free for 30 days · Plan by order volume · On-premise) —
   leave the amounts as "Liên hệ" (Contact us) if not yet decided, but the structure and the pilot terms must be clear.
7. Add a /security page: where data is stored, encryption, permissions, audit log, compliance with Decree 13/2023
   on personal data protection, the on-premise option, and the data deletion process when the contract ends.

## Acceptance criteria
  a) GET / does not contain the class "sidebar"; GET /orders when not logged in → redirect to /login.
  b) grep apps/web and docs/ no longer finds "SOX", "SOC2", "Zero-Hallucination", "99.4", "popreflight.com",
     "po-preflight.vn", "09xx".
  c) a valid POST /leads → 201 and a row exists; honeypot filled → a fake 200 (not saved); 6 requests/minute → 429.
  d) Lighthouse SEO ≥ 90 for "/", robots blocks /orders.
  e) Landing screenshots at 1280 & 375 have no overlapping elements.

## Deliverables
- Commit: "fix(marketing): separate landing from app, truthful claims, unified contact, lead capture, pricing & security pages"
```

---

## PROMPT A9 — Consistent configuration, CI, deploy

**Branch:** `fix/a9-config-ci`

```
## Objective
Environment variables declared in .env.example are not read; the deploy ports are inconsistent; the Python versions are inconsistent;
CI does not run the FE; deploy does not package the web app.

## Evidence
- .env.example: PREFLIGHT_DB_PATH, CATALOG_PATH — src/ does not read them (deps.py hardcodes them)
- scripts/deploy-remote.sh:16 curl :8000 — Makefile/Docker use 8001
- .venv Python 3.14; CI 3.11/3.12; Dockerfile 3.11
- .github/workflows/deploy.yml tars only src tests examples scripts
- scripts/test.sh runs npm only "if command -v npm"

## Requirements
1. Create src/preflight/config.py using pydantic-settings: Settings(env, auth_required, database_url,
   catalog_path, upload_dir, session_secret, cors_origins, telegram_*, zalo_*, gemini_*, erp_*,
   fx_live, rate_limit_enabled, company_name, smtp_*). Replace every os.getenv in src/ with
   get_settings(). Validate at startup: production missing session_secret / webhook secret / api key
   → exit with a message listing what is missing. Print the configuration table (secrets masked) at startup.
2. .env.example matches Settings 1-to-1 (auto-generated by the script scripts/gen_env_example.py, with a test
   that checks they match).
3. Pin Python: pyproject requires-python ">=3.12,<3.13"; CI matrix ["3.12"]; Dockerfile 3.12;
   .python-version 3.12; README instructions.
4. The Makefile PORT and deploy-remote.sh both read PORT (default 8001); a sample systemd unit
   infra/systemd/po-preflight.service uses EnvironmentFile=/etc/po-preflight.env.
5. CI (.github/workflows/ci.yml): a backend job (unittest + ruff check + mypy --strict for
   services/, rules*.py, erp/payload.py), a frontend job (npm ci, tsc, lint, npm test, playwright
   with the backend running in the background), a docker build job. Add ruff + mypy to [project.optional-dependencies].dev.
6. Deploy: package the whole apps/web/dist (built in CI) or switch to a docker image pushed to GHCR +
   compose pull on the server. Choose docker; deploy-remote.sh runs `docker compose pull && up -d`
   and then checks /health/ready on PORT.
7. Terraform: add RDS Postgres (db.t4g.micro), an S3 bucket for uploads (private, SSE), Secrets Manager
   for the env; EC2 user-data installs docker. Keep costs to a minimum; the variable `enable_rds` defaults to false.
8. Remove .cursor/ and .agents/ from the repo if they are unused; keep AGENTS.md but update the "Frontend
   Stack" section (auth/landing have changed).

## Acceptance criteria
  a) PREFLIGHT_ENV=production without SESSION_SECRET → startup exit code ≠0, the log lists the missing variables.
  b) CATALOG_PATH pointing to a different file → /catalog returns the data of that file.
  c) CI is green for all 3 jobs; playwright runs in CI.
  d) `python scripts/gen_env_example.py --check` passes.
  e) the docker build succeeds with Python 3.12; the image serves /health/ready 200.

## Deliverables
- Commit: "chore(config,ci): typed settings, single Python version, full-stack CI, docker-based deploy"
```

---

# PHASE B — P1: GET THE VIETNAMESE DISTRIBUTOR BUSINESS DOMAIN RIGHT

Phase goal: a Sales Admin at an FMCG/pharmaceutical distributor can use it for 2 weeks without running into "the system doesn't understand my order".

---

## PROMPT B1 — Data model v2 and migration runner

**Branch:** `feat/b1-data-model-v2`

```
## Objective
The store is currently 1,342 lines hand-maintaining 2 SCHEMA strings, with no migrations, line items buried in order_json,
no customers, and no revisions. Move to SQLAlchemy Core + Alembic with a relational schema.

## Evidence
- src/preflight/store.py:24-195   SQLITE_SCHEMA & POSTGRES_SCHEMA maintained in parallel
- ux_analyses_po UNIQUE(po_number) is global
- dashboard.py:26-45 loads 500 rows and parses JSON to count findings

## Requirements
1. Add dependencies: sqlalchemy>=2.0, alembic>=1.13. Create src/preflight/db/ (engine.py, models.py
   using SQLAlchemy Core Table, no ORM session so the store stays explicit), src/preflight/migrations/
   (alembic.ini, env.py, versions/). Engine from Settings.database_url; SQLite enables WAL + foreign_keys.
2. Schema v2 (Alembic 0001_baseline creates from empty; 0002_import_legacy reads the old tables if they exist):
   - organizations(id, code, name, created_at)  -- prepares for multi-tenancy; every business table has org_id
   - users(id, org_id, username, display_name, email, password_hash NULL, role, is_active, created_at)
   - api_keys(id, user_id, key_hash, label, last_used_at, revoked_at)
   - channel_identities(id, user_id, channel, external_id, created_at) UNIQUE(channel, external_id)
   - customers(id, org_id, code, name, normalized_name, tax_code NULL, tier NULL, created_at)
     UNIQUE(org_id, code)
   - customer_aliases(id, customer_id, alias_normalized) UNIQUE(customer_id, alias_normalized)
   - products(id, org_id, sku, name, unit_price, stock, active, base_uom, moq, pack_size, category,
     barcode, updated_at) UNIQUE(org_id, sku)   -- the catalog moves into the DB; CSV becomes the import source
   - uom_conversions(id, product_id, uom_code, factor) UNIQUE(product_id, uom_code)
   - customer_prices(id, customer_id, product_id, contract_price, min_quantity, discount_percent,
     valid_from, valid_to) 
   - customer_credits(customer_id PK, credit_limit, outstanding_balance, overdue_balance,
     oldest_overdue_days, status, updated_at, source)
   - orders(id, org_id, customer_id, po_number, revision INT DEFAULT 1, supersedes_order_id NULL,
     status, rule_status, currency, subtotal, tax_amount, grand_total, source_file, source_path,
     source_channel, created_by, created_at, analyzed_at)
     UNIQUE(org_id, customer_id, po_number, revision)
   - order_lines(id, order_id, line_no, raw_sku, sku, product_id NULL, description, quantity, uom,
     base_quantity, unit_price, discount_percent, discount_amount, tax_rate, is_promo, line_total)
   - findings(id, order_id, line_id NULL, code, severity, message, evidence_json)
   - decisions(id, order_id, decision, actor_user_id, channel, note, created_at)
   - audit_blocks(...) as before + order_id, request_id
   - erp_outbox(...) as in A3 + order_id, next_attempt_at
   - rule_policies(org_id PK, policy_json, updated_by, updated_at)
   - sku_alias_learning(id, customer_id, raw_query_normalized, product_id, confidence, created_at)
   - leads(...) from A8
   status (lifecycle) is separated from rule_status (rule outcome): status ∈ {received, extraction_review,
   analyzed, approved, rejected, needs_changes, superseded, exported}; rule_status ∈
   {ready_for_approval, review_required, blocked}. They no longer overwrite each other.
3. Rewrite the store into small repositories in src/preflight/repositories/: orders.py, customers.py,
   products.py, decisions.py, audit.py, outbox.py, policies.py, users.py. Each repo receives a Connection.
   BaseAuditStore is kept as a temporary compatibility facade for the old routes, marked deprecated, and deleted at the end of B.
4. Unit of work: routes use the dependency `get_db()`, which yields a Connection within a transaction; commit on
   success, rollback on exception. No more scattered connection.commit.
5. Legacy data migration (0002): analyses → orders+order_lines (customers created by normalized_name,
   auto-generated codes C0001…), findings_json → findings, decisions map the actor string → temporary users
   (username = actor), audit_blocks kept. Provide the script `preflight db upgrade` (CLI) and `preflight db
   check` (schema vs metadata).
6. get_dashboard_stats uses SQL GROUP BY on findings/orders; no JSON parsing.
7. Dev seed: `preflight seed-demo` creates the org "demo", 3 customers, a catalog from CSV, and 4 sample orders — replacing
   seed_initial_data in the lifespan (no automatic seeding in production).

## Acceptance criteria
  a) `alembic upgrade head` on empty SQLite and on Postgres (TEST_DATABASE_URL) both succeed;
     `alembic check` shows no drift.
  b) Old DB (fixture tests/fixtures/legacy_preflight.db) → upgrade → the number of orders, decisions, and
     audit blocks match; order_lines has the correct number of rows.
  c) All existing tests pass via the facade; new tests for the repositories.
  d) Customer A and customer B with the same po_number "PO-001" → 2 separate orders, no error.
  e) dashboard/stats returns the same figures as a verifying SQL query in the test.
  f) No SQLITE_SCHEMA/POSTGRES_SCHEMA strings remain in src/.

## Deliverables
- Commit: "feat(db): relational schema v2 with Alembic migrations, repositories, legacy import"
```

---

## PROMPT B2 — Line item v2: VAT, discounts, promotions, UOM

**Branch:** `feat/b2-line-item-v2`

```
## Objective
Vietnamese POs carry 8/10% VAT, line/order discounts, zero-price promotional goods, and shipping fees. The engine
currently computes total = Σ qty×price, tax=0, and a price of 0 → 100% PRICE_MISMATCH.

## Requirements
1. Domain (models.py): LineItem adds discount_percent (Decimal, 0-100), discount_amount (Decimal),
   tax_rate (Decimal: 0, 5, 8, 10), is_promo (bool), description (str|None), uom (already exists), raw_sku.
   line_net = qty×unit_price − discount_amount − qty×unit_price×discount_percent/100;
   line_tax = line_net × tax_rate/100; line_total = line_net + line_tax.
   Order adds header_discount_amount, shipping_fee, declared_subtotal, declared_tax, declared_total
   (from the document, may be None); the properties subtotal, tax_amount, grand_total are computed from the lines + header.
2. Parsers:
   - JSON: accept the new fields (optional).
   - CSV: optional columns discount_percent, discount_amount, tax_rate, is_promo, uom, description.
   - Excel: extend the aliases: "chiết khấu" (discount), "ck" (discount, abbreviated), "% ck" (discount %), "giảm giá" (price reduction), "thuế" (tax), "vat", "thuế suất" (tax rate),
     "tiền thuế" (tax amount), "khuyến mãi" (promotion), "km" (promotion, abbreviated), "tặng" (free gift), "hàng tặng" (free goods), "phí vận chuyển" (shipping fee), "phí ship" (shipping fee), "tổng trước
     thuế" (total before tax), "tổng sau thuế" (total after tax), "cộng tiền hàng" (goods subtotal). Recognize promotional lines: price 0 or a description containing
     "KM"/"tặng"/"khuyến mãi" → is_promo=True. Read the declared total from the cells "Tổng cộng/Thành tiền/
     Tổng thanh toán" (Total / Amount / Total payment) (the last numeric cell at the bottom of the table). Accept numbers in the forms "1.250.000", "1,250,000", "1.250.000,50", "1 250 000".
   - OCR prompt: require it to return discount, tax_rate, is_promo per line; declared_* in the header.
3. SelfReflectionVerifier: compare declared_total with the computed grand_total; tolerance = max(1,000 VND, 0.5%);
   distinguish 3 outcomes: match / deviation due to tax rounding (<1% and correct when recomputed with per-line
   rounding) / true deviation. The result is attached to the Order as a finding TOTAL_MISMATCH (warning), not
   only inside ExtractedOrder.
4. rules.py:
   - PRICE_MISMATCH compares unit_price (before discount, before tax) with the expected price; is_promo=True → skip
     the price comparison, replaced by a finding PROMO_LINE (info — add severity "info" to Finding, the FE displays it in grey).
   - Add DISCOUNT_EXCEEDS_POLICY (warning): discount_percent > policy.max_discount_percent (default 15).
   - Add TAX_RATE_INVALID (error) when tax_rate is not in {0,5,8,10}.
   - Every monetary message uses the order's currency (no hardcoded VND).
5. FE types/derive/UI: LineItem adds the fields; the line items table adds the columns `CK` (Discount), `Thuế` (Tax), `Thành tiền` (Line total);
   FINDING_TITLE for the new codes; severity "Info".
6. examples: add po-vat-discount.xlsx and .json showing all of the above.

## Acceptance criteria
  a) An Excel with 10% VAT + 5% discount + 1 free line at price 0 → grand_total exact to the last dong; the free line yields
     PROMO_LINE, not PRICE_MISMATCH; TOTAL_MISMATCH does not fire when the totals match.
  b) declared_total off by 2 million → TOTAL_MISMATCH warning with the deviation amount.
  c) tax_rate 7 → TAX_RATE_INVALID error → blocked.
  d) The number "1.250.000,50" parses to Decimal("1250000.50").
  e) A USD order → the message contains "USD".

## Deliverables
- Commit: "feat(domain): line items with discount/VAT/promo, Vietnamese Excel aliases, total verification as finding"
```

---

## PROMPT B3 — Rules v2: contracts with validity periods, configurable credit, finding code registry

**Branch:** `feat/b3-rules-v2`

```
## Requirements
1. Contract price: check valid_from/valid_to against the order date (order_date from the document, falling back to the
   receipt date); pick the highest min_quantity tier that is satisfied; expired → CONTRACT_PRICE_EXPIRED (warning) and compare
   against the catalog price.
2. Credit: thresholds configurable in RulePolicy: overdue_grace_days (default 30), credit_limit_block_percent
   (default 20), credit_hold_behaviour ("block"|"review"). ON_HOLD → CUSTOMER_ON_HOLD (warning).
   Exposure = outstanding + grand_total (after tax). Messages use the order currency; if the order is in a different currency
   from credit_limit → convert via ctx.fx_rates, stating the exchange rate.
3. Duplicate: moved to B4.
4. Stock: use ctx.available_stock(product) (B7 will provide ATP; for now = stock − safety_margin).
5. Registry: src/preflight/findings_registry.py — a list of FindingSpec(code, default_severity,
   title_vi, description_vi, category ∈ {catalog, price, stock, credit, document, duplicate, fx})
   as the single source; rules.py creates a Finding only through registry.make(code, **fmt). Generate
   apps/web/app/lib/findings.generated.ts with the script scripts/gen_findings_ts.py; CI checks for drift.
6. Rule explainability: Finding adds evidence: dict (expected, actual, source, rule_version).
   Example PRICE_MISMATCH: {"po_price":"17600000","expected_price":"18500000","source":"catalog",
   "tolerance_percent":"0","rule_version":"2.0"}. The FE displays a table `Kỳ vọng / Thực tế / Nguồn` (Expected / Actual / Source)
   in place of the hardcoded string "Grounding rule … Catalog v2026.08".
7. RulePolicy has a version; each Analysis stores policy_version and catalog_snapshot_at for reproducibility
   (PRD FR-027/FR-053).

## Acceptance criteria
  a) a contract that expired yesterday → CONTRACT_PRICE_EXPIRED + PRICE_MISMATCH against the catalog.
  b) a 45-day grace in the policy → a 40-day debt does not yield OVERDUE_DEBT_BLOCKED; with 30 → it does.
  c) ON_HOLD → review_required, not blocked.
  d) gen_findings_ts --check passes; the FE uses titles from the generated file, delete the manual FINDING_TITLE.
  e) every finding over HTTP has evidence as an object with ≥2 keys.

## Deliverables
- Commit: "feat(rules): contract validity, configurable credit policy, findings registry with structured evidence"
```

---

## PROMPT B4 — Resubmit a PO as a revision; duplicates in the true sense

**Branch:** `feat/b4-revisions-duplicates`

```
## Objective
Currently, when a customer corrects and resends the same PO number → IntegrityError → marked DUPLICATE_PO, blocked. The
"Request changes → resubmit" loop cannot happen. At the same time we need to detect true duplicates (same customer, same
goods, sent through 2 channels).

## Requirements
1. Upload/ingest when (customer_id, po_number) already exists:
   - Old order in needs_changes / rejected / extraction_review → create revision+1, old order → superseded,
     supersedes_order_id points back to it; NO DUPLICATE_PO finding; add a finding REVISED_ORDER (info) stating the
     differences (lines added/removed/qty changed/price changed) via a normalized diff.
   - Old order in approved / exported → DUPLICATE_PO (error) as today, with evidence linking to the old order.
   - Old order in analyzed/received (no decision yet) → ask: query parameter ?on_conflict=revise|reject
     (default reject → 409 DUPLICATE_PENDING with a hint). The UI shows the dialog "Đơn này đang chờ duyệt.
     Thay bằng bản mới?" (This order is awaiting approval. Replace it with the new version?).
2. Near-duplicate: after analysis, find orders of the same customer within 14 days with Jaccard(set(sku,qty)) ≥ 0.9
   and |total diff| < 1% → POSSIBLE_DUPLICATE (warning) with the list of suspected duplicate POs.
3. The superseded status is not shown in the default queue; the order detail has a section "Các phiên bản" (Versions)
   listing the revision, who submitted it, and what differs.
4. DecisionService: needs_changes additionally stores `requested_changes` (text) and sends a notification (Telegram/
   Zalo if the order's creator has an identity; email if C1 is done) — currently it only writes to the DB.
5. UI: the button "Tải bản sửa" (Upload revised version) on a needs_changes order opens the UploadModal with po_number pre-filled.

## Acceptance criteria
  a) upload → needs_changes → upload the same PO again with a different qty → revision 2, the old one superseded, has REVISED_ORDER
     stating "LAPTOP-A14: 10 → 8".
  b) re-upload an already approved PO → DUPLICATE_PO error.
  c) while the order is analyzed, re-upload with no parameter → 409 DUPLICATE_PENDING; with on_conflict=revise → revision 2.
  d) 2 different customers with the same "PO-001" → unrelated.
  e) same customer, a different PO number, the same 3 lines with the same qty within 3 days → POSSIBLE_DUPLICATE.

## Deliverables
- Commit: "feat(orders): PO revisions replace hard duplicate block; near-duplicate detection"
```

---

## PROMPT B5 — Customer master and alias learning by ID

**Branch:** `feat/b5-customer-master`

```
## Requirements
1. CRUD API /api/v1/customers (MANAGER): code, name, tax_code, tier, aliases[]. CSV import
   (code,name,tax_code,tier,aliases using ";").
2. Customer resolver on ingest: src/preflight/services/customer_resolver.py:
   - Normalize the name (remove diacritics, uppercase, remove the business entity type, remove special characters) → look up
     customers.normalized_name and customer_aliases; look up tax_code if the document has a tax ID (Excel/OCR extracts
     "Mã số thuế"/"MST" (tax code)).
   - No exact match → RapidFuzz token_set_ratio ≥ 90 → match with a finding CUSTOMER_FUZZY_MATCHED
     (warning, evidence: original name, chosen customer, score); < 90 → the order goes into extraction_review with
     CUSTOMER_UNRESOLVED (error) and the UI lets the user choose a customer / create a new one. When the user chooses → save the alias.
3. SKU alias learning (the old customer_aliases) moves to sku_alias_learning by customer_id;
   HybridSKUMatcher Tier-0 looks up by customer_id. Remove the hardcoded CUSTOMER_HISTORICAL_NICKNAMES in
   rag/llm_fallback.py; Tier-4 looks up sku_alias_learning + the customer's order_lines history (raw_sku →
   confirmed sku) before calling the LLM.
4. Contract price, credit, and aliases are all keyed by customer_id; remove the temporary normalize_customer_key from A1.
5. UI: a `Khách hàng` (Customers) page (Sales Admin): list, detail (contract prices, credit/receivables, learned SKU aliases,
   order history). Staging: a dropdown to choose a customer when CUSTOMER_UNRESOLVED.

## Acceptance criteria
  a) "CTY TNHH ABC" and "Công ty TNHH A.B.C" → the same customer after normalization; "ABC Trading" → fuzzy 90+.
  b) an unknown name → extraction_review + CUSTOMER_UNRESOLVED; confirming by choosing a customer → alias saved; next time it matches at Tier-0.
  c) the line "dây mạng 3m" (3m network cable) corrected by the user to CAB-CAT6-3M for customer X → next time customer X matches
     at Tier-0, customer Y does not.
  d) grep src/ no longer finds "NORTHSTAR", "VINGROUP", "ACME".

## Deliverables
- Commit: "feat(customers): customer master, resolver with fuzzy match, per-customer SKU alias learning"
```

---

## PROMPT B6 — Users, passwords, value-based approval matrix

**Branch:** `feat/b6-users-approval-matrix`

```
## Requirements
1. Users have password_hash (argon2 via `argon2-cffi`), POST /auth/login {username,password}; an API key
   is an alias of a user (api_keys). The env PREFLIGHT_*_KEY is used only to bootstrap the admin the first time (create the
   admin user if the table is empty), and is disabled afterwards. CLI `preflight users create/reset-password/list`.
2. Roles: viewer, sales_admin (upload, edit extraction, request changes), manager (approve up to a limit),
   director (approve any amount), auditor (read the log), admin. Update RBAC.
3. Approval matrix in RulePolicy: tiers = [{max_amount: 50_000_000, min_role: manager},
   {max_amount: null, min_role: director}]; additional condition: a finding CREDIT_LIMIT_EXCEEDED →
   min_role director. DecisionService checks: the role is sufficient for the grand_total and findings; insufficient → 403
   APPROVAL_LEVEL_INSUFFICIENT with the message "Đơn {total} cần cấp {role}" (Order {total} requires the {role} level). Notification routing:
   hitl_dispatch sends to users with an appropriate role (channel_identities).
4. Separation of duties: the person who created/edited an order may not approve that same order (policy on/off, default on).
5. UI: a User administration page (admin); the approval modal displays "Cần cấp: Trưởng phòng/Giám đốc" (Required level: Department head/Director).

## Acceptance criteria
  a) a manager approves an 80-million order with the 50-million tier → 403 APPROVAL_LEVEL_INSUFFICIENT; a director → 200.
  b) a sales_admin uploads an order and then approves it themselves → 403 (SoD).
  c) logging in with the wrong password 5 times → locked for 15 minutes (429).
  d) the old env key can no longer be used once users exist (except for bootstrap).

## Deliverables
- Commit: "feat(auth): users with passwords, role hierarchy, amount-based approval matrix, separation of duties"
```

---

## PROMPT B7 — Inventory source from the ERP, and ATP

**Branch:** `feat/b7-inventory-atp`

```
## Requirements
1. The interface erp/adapters/base.py adds `fetch_inventory(skus: list[str] | None) -> list[InventorySnapshot]`
   (sku, warehouse, on_hand, reserved, as_of). Mock adapters read CSV; live adapters (Odoo stock.quant,
   MISA inventory API, SAP MaterialStock) implement at minimum Odoo + MISA (MISA may not have been tested
   for real → clearly dry_run mode).
2. Table inventory_snapshots(product_id, warehouse, on_hand, reserved, as_of, source). The job
   `preflight inventory sync` (CLI; C2 will schedule it) writes snapshots; products.stock = Σ on_hand.
3. ATP = on_hand − reserved_erp − allocated_local, where allocated_local = Σ base_quantity of the
   order_lines belonging to orders with status approved and not yet exported (outbox not yet SENT). When the outbox is SENT → the order
   becomes exported → it is no longer counted (the ERP has already deducted it). When rejected/superseded → not counted.
4. RuleContext.available_stock(product) uses ATP; the INSUFFICIENT_STOCK evidence includes on_hand, reserved,
   allocated_local, as_of. If the snapshot is older than policy.inventory_stale_hours (default 24) →
   INVENTORY_STALE (warning).
5. Catalog UI: a column "Tồn khả dụng" (Available stock) and the last-updated time; a stale warning.

## Acceptance criteria
  a) stock 10; order A approved for 6 and not yet exported; order B for 5 → INSUFFICIENT_STOCK (ATP 4).
  b) order A exported → a new order B has no finding (simulated snapshot with on_hand 4).
  c) a 30-hour-old snapshot → INVENTORY_STALE.

## Deliverables
- Commit: "feat(inventory): ERP inventory snapshots and available-to-promise with local allocations"
```

---

## PROMPT B8 — Real observability

**Branch:** `feat/b8-observability`

```
## Requirements
1. Logging: structlog or logging.config with a JSON formatter when PREFLIGHT_LOG_FORMAT=json (the default
   in production), colored output in dev. Every log has request_id, user_id, order_id (contextvars). Strip ANSI
   in production.
2. request_id propagation: audit_blocks.request_id, erp_outbox.request_id, decisions.request_id;
   the X-Request-ID header is returned on every response, errors included.
3. OpenTelemetry (optional deps `otel`): FastAPI instrumentation, spans for parse/rules/sku_resolve/
   erp_sync/ocr; an OTLP exporter when OTEL_EXPORTER_OTLP_ENDPOINT is present, otherwise off.
4. Sentry optional (SENTRY_DSN).
5. Metrics: record_order_processed and record_sku_resolution are currently called by nobody → call them in the right places;
   add an analysis-time histogram, a count of findings by code, and the age of pending outbox items.
6. An admin page /admin/health in the UI: modes, DB, outbox pending/dead-letter, age of the inventory snapshot,
   the 10 most recent 5xx errors (table request_errors, retained for 7 days).
7. Runbook docs/RUNBOOK.md: how to trace a request_id from an error toast → log → audit; how to handle DEAD_LETTER;
   how to rotate a secret; how to restore the DB.

## Acceptance criteria
  a) the JSON log has a request_id matching the response header and matching audit_blocks.request_id for the same upload.
  b) /metrics has po_preflight_findings_total{code=...} after an upload.
  c) a simulated 500 error appears in /admin/health.

## Deliverables
- Commit: "feat(observability): structured logs with request correlation, OTel/Sentry optional, real metrics, runbook"
```

---

# PHASE C — P2: PILOT READY

Goal: a real distributor uses it for 30 days; pilot figures replace claims.

---

## PROMPT C1 — Receive POs by email

**Branch:** `feat/c1-email-intake`

```
## Requirements
1. Service src/preflight/intake/email.py: connect via IMAP (env IMAP_HOST/USER/PASSWORD/FOLDER, or the
   Gmail API with OAuth if GOOGLE_* is present), poll the mailbox every N minutes (C2 schedules it; CLI `preflight intake
   email --once`), fetch unread mail that has attachments .xlsx/.xls/.csv/.pdf/.png/.jpg/.json.
2. Each attachment → the ingest pipeline as an upload; source_channel="email", metadata: from, subject,
   message_id (UNIQUE for idempotency), received_at. The sender (email) → look up customers (add the column
   contact_emails) → customer_id; no match → CUSTOMER_UNRESOLVED.
3. Mail without a valid attachment → label/move to the folder "preflight-ignored"; a parse error → an automatic
   email reply (Vietnamese template) "Chúng tôi không đọc được file … vui lòng gửi Excel theo
   mẫu đính kèm" (We could not read the file … please send an Excel file following the attached template) + attach the standard Excel template examples/templates/PO_MAU.xlsx
   (newly created; `MAU` = sample/template).
4. After analysis → notify the approval channel as with a web upload; reply to the email confirming "Đã nhận PO {po},
   mã theo dõi {id}" (Received PO {po}, tracking code {id}).
5. UI: the "Email" source shows the sender, the subject, and a link to download the original file; Settings: mailbox status,
   last poll time, number of failed emails.

## Acceptance criteria (use a simulated IMAP server in tests, e.g. an `aioimaplib` mock or GreenMail
via docker in CI)
  a) 1 mail with 2 xlsx attachments → 2 orders; resending the same message_id → nothing more is created.
  b) a mail with only a .docx → moved to ignored + an auto-reply with the template.
  c) a sender present in contact_emails → the correct customer.

## Deliverables
- Commit: "feat(intake): IMAP/Gmail email ingestion with idempotent processing and auto-reply"
```

---

## PROMPT C2 — Background job queue and Redis

**Branch:** `feat/c2-job-queue`

```
## Requirements
1. Add `arq` + Redis (env REDIS_URL). Jobs: analyze_order(order_id), run_ocr(order_id),
   outbox_dispatch(), inventory_sync(), email_poll(), notify(order_id). Worker: `preflight worker`.
   Cron: outbox every 1 minute, inventory every 30 minutes, email every 2 minutes (configurable).
2. Upload: if the file needs OCR (SCANNED_PDF/IMAGE) → create an order with status received, enqueue run_ocr, return
   202 with order_id; the UI displays "Đang bóc tách…" (Extracting…) and updates via SSE. Deterministic files are still
   processed synchronously (fast) but through the same service function so there is a single code path.
3. EventBus: when REDIS_URL is present → Redis pub/sub so that multiple uvicorn workers can emit SSE together; when absent →
   in-memory (dev) and /system/modes records "sse":"single_process".
4. Rate limiter: Redis-backed when Redis is present.
5. Graceful shutdown; job retry with backoff; dead-letter jobs write to request_errors.

## Acceptance criteria
  a) upload a PNG → 202, after the worker runs → status analyzed, SSE receives "order.analyzed".
  b) 2 uvicorn processes + Redis: SSE from process A receives an event created in process B (docker integration test).
  c) the worker dies in the middle of outbox_dispatch → the event returns to PENDING after the lease timeout, is not lost, and is not sent twice.

## Deliverables
- Commit: "feat(infra): arq job queue, Redis-backed SSE and rate limiting, async OCR"
```

---

## PROMPT C3 — Real MISA AMIS connector (or the ERP chosen for the pilot)

**Branch:** `feat/c3-misa-live`

```
## Precondition: a MISA AMIS sandbox account is available (or the pilot ERP: Bravo/Fast/Odoo).
If not → STOP, do not write code that "guesses" the API. Record in docs/erp/MISA.md what is needed from the customer.

## Requirements (once the sandbox is available)
1. Read the official API documentation; record the auth endpoint, create sales order, inventory lookup, customer lookup, and error codes in
   docs/erp/MISA.md. Fix misa_live.py to match the real documentation (the URL "https://api.misa.vn/amis/v1" is currently
   a guess).
2. Mapping: customer → account_object (look up by tax_code/code, create if policy allows), sku →
   inventory_item_code, uom, tax_rate, discount; header: the PO number goes into the reference field; a note
   "PO Preflight #{order_id}".
3. Contract tests with the sandbox (run when MISA_SANDBOX_TOKEN is present): create a 3-line order → read it back → compare
   field by field; send a duplicate idempotency key → does not create 2.
4. Reconciliation job: every hour compare outbox SENT items with the ERP (does it exist? do the totals match?) → a mismatch → a system
   finding RECONCILIATION_MISMATCH in /admin/health and notify the admin.
5. ERP Outbox UI: a link to open the document in the ERP, a "Đối soát ngay" (Reconcile now) button.

## Deliverables
- Commit: "feat(erp): MISA AMIS live connector verified against sandbox, reconciliation job"
```

---

## PROMPT C4 — Real Zalo OA and Telegram for managers

**Branch:** `feat/c4-channels-live`

```
## Requirements
1. Zalo OA: read the official OA v3 documentation; the payload currently uses the "media" template with an oa.query.show button —
   verify which message types may be sent to users who have not followed / are outside the 48h window (ZNS needs an approved template).
   Implement: (a) OA interactive messages for users who have followed, (b) a ZNS template "PO cần duyệt" (PO awaiting approval) (register the
   template, store template_id in Settings). Automatic token refresh (the function already exists) + store the tokens in the DB
   (table channel_tokens, encrypted with SESSION_SECRET).
2. Zalo webhook: verify the signature per the documentation (the formula sha256(app_id+body+timestamp+secret) is currently
   a guess — re-check it), prevent replay (timestamp ±5 minutes, store the processed event_ids).
3. Telegram: handle the callback by calling answerCallbackQuery (currently not called → the button spins forever); update the
   message after the decision ("✅ Đã duyệt bởi Nguyễn A lúc 10:32" (Approved by Nguyễn A at 10:32)); the command /link <code> to self-link an
   account (the code is generated in the user's Settings UI).
4. Notification card: displays grand_total after tax, the number of findings by severity, the first 3 findings in Vietnamese,
   a deep link into the order (requires login).
5. Escalation: an order waiting > policy.escalation_hours (default 4) → remind again; > 24h → send to the superior.

## Acceptance criteria
  a) Telegram: pressing approve → answerCallbackQuery is called (mock HTTP), the message is edited.
  b) Zalo webhook replay with the same event_id → ignored.
  c) /link with the correct code → channel_identities has a record; a code that has expired after 10 minutes → error.
  d) Manual test with 1 real Zalo/Telegram account, record screenshots in the PR.

## Deliverables
- Commit: "feat(channels): production Zalo OA/ZNS flow, Telegram callback UX, self-service account linking, escalation"
```

---

## PROMPT C5 — Real embeddings for Tier-3 and a per-customer eval set

**Branch:** `feat/c5-real-embeddings`

```
## Requirements
1. Replace VectorSemanticMatcher (bag-of-words + a hand-built synonym map) with multilingual embeddings running locally:
   `fastembed` with the model BAAI/bge-m3 (or intfloat/multilingual-e5-small if a lightweight option is needed). Index
   in SQLite (table product_embeddings, vector blob) with brute-force cosine (a catalog < 50k SKUs is fast
   enough) — ChromaDB is not needed yet. Update docs: remove "ChromaDB", "TF-IDF trigram".
2. Embedded text = sku + name + category + learned aliases + description. Rebuild when the catalog changes (job).
3. Thresholds: computed from eval (item 5), do not hardcode 0.35/0.70.
4. Tier-4 LLM: use Gemini via the official SDK (google-genai) with structured output; timeout, retry,
   circuit breaker; log token usage; call it only when Tiers 0–3 are below the threshold; always constrain the return to a SKU in the
   top-20 candidate list (not the whole catalog — currently the whole catalog is sent every time).
5. Eval: expand evals/ground_truth.json → evals/<customer>/aliases.jsonl (raw, expected_sku) collected
   from real pilot data (anonymized). scripts/run_evals.py prints precision@1, recall, the rate of falling through to
   Tier-4, and cost; saves evals/results/<date>.json; CI fails if precision@1 drops by more than 2 points versus the
   baseline.
6. The UI "Công cụ kiểm thử SKU" (SKU testing tool) (admin) displays 3 candidates with scores and tier; a button "Đúng là mã này" (This is the right code) →
   writes alias learning.

## Acceptance criteria
  a) "dây mạng 3m bấm sẵn" (3m network cable, pre-crimped) → CAB-CAT6-3M top-1 with embeddings, no synonym map needed.
  b) run_evals on the existing set ≥ baseline; the report includes the Tier-4 rate.
  c) Gemini error → the circuit goes OPEN after 3 failures, and resolve returns unresolved immediately with the reason "LLM tạm ngưng" (LLM temporarily suspended).

## Deliverables
- Commit: "feat(rag): local multilingual embeddings for tier-3, constrained LLM tier-4, evaluation harness"
```

---

## PROMPT C6 — Pilot-ready frontend

**Branch:** `feat/c6-frontend-pilot`

```
## Requirements
1. Orders screen: edit line items inline within the detail view for extraction_review /
   needs_changes orders: change the SKU (a searchable dropdown calling /sku/resolve), qty, price, UOM; "Lưu & chạy lại
   kiểm tra" (Save & re-run checks) → confirm-extraction. No more standalone Staging Studio — merge it into the order detail.
2. View the original document: PDF.js (cdnjs) renders pages, images are zoomable; for OCR with bounding boxes (if Gemini returns
   them) → highlight the line on hover.
3. Queue table: sorting, filtering by customer/status/date/severity, server-side pagination
   (the list API has total), save the filters in the URL.
4. Empty, loading, and error states for every screen; error toasts have a "Mã tham chiếu" (Reference code) (request_id) and a
   copy button.
5. Accessibility: focus trap + Escape for modals, aria-live for toasts, WCAG AA contrast check for both
   themes (an automated check script in the tests).
6. Mobile: a minimal approval screen /m/orders/{id} for managers opening from Telegram/Zalo: total, findings, 3 buttons.
7. Remove from the customer nav: LangGraph Visualizer, RAG Tester, Merkle Certificate → /admin/tools.
   Rename "Merkle Certificate" → "Chứng thư nhật ký (chuỗi băm SHA-256)" (Audit log certificate (SHA-256 hash chain)).
8. Playwright: 6 journeys: login; upload an Excel with VAT/discounts → fix the SKU inline → approve (manager) → blocked
   by the limit → director approves → view the outbox; resubmit a needs_changes PO; mobile approve.

## Acceptance criteria
- Playwright 6/6 green in CI; axe-core has no serious/critical errors; tsc/lint clean.

## Deliverables
- Commit: "feat(web): inline extraction correction, source viewer, server-side queue, mobile approval, a11y"
```

---

## PROMPT C7 — Pilot measurement

**Branch:** `feat/c7-pilot-metrics`

```
## Requirements
1. Measurement events (a metrics_events table, or derived from existing data): time from received → analyzed; from
   analyzed → decision; number of lines edited by people / total lines; number of findings by code; number of orders blocked before the ERP;
   number of DUPLICATE/POSSIBLE_DUPLICATE; LLM/OCR cost per order; the RAG Tier rate.
2. GET /api/v1/reports/pilot?from&to (MANAGER) returns JSON; /reports/pilot.csv; a "Báo cáo" (Reports) page in the UI
   with simple charts (hand-drawn SVG, no heavy library).
3. An automatic weekly email to the admin (Vietnamese template) when SMTP is present.
4. docs/PILOT_PLAYBOOK.md: pilot goals per PRD §18, how to read the report, a 30-day checklist,
   a Sales Admin interview template after weeks 1/2/4.

## Deliverables
- Commit: "feat(reports): pilot KPI report, CSV export, weekly email, pilot playbook"
```

---

## PROMPT C8 — Evidence-based documentation and marketing

**Branch:** `docs/c8-truthful-marketing`

```
## Requirements
1. README, docs/MO_TA_DU_AN.md (project description), docs/architecture.md: update them to the true current state (a table "Component |
   Status: live / dry-run / planned"). Remove "MIT Outer System / Stanford Inner Loop",
   "Merkle", "ChromaDB", "WeChat" from the description of the current state (they may be kept in a "Vision" section if desired).
2. Pitch deck & one-pager: replace the fake ROI table with "Kết quả pilot {khách}: … " (Pilot results for {customer}: …) once available; until then use
   "Cách chúng tôi đo" (How we measure) in place of figures. Remove SOX/SOC2; add Decree 13, on-prem, and the data handling process.
   ICP and ERP: MISA/Bravo/Fast/Odoo/SAP B1.
3. Pricing: complete /pricing with specific figures after 2 pricing interviews (record the assumptions).
4. Demo video: re-record it on real data from the A7/C6 flow (not a mock); the script in
   docs/marketing/VIDEO_DEMO_60S_SCRIPT.md is updated.
5. Case study template docs/marketing/CASE_STUDY_TEMPLATE.md: context, before/after, figures from C7,
   customer quotes.
6. Technical sales material docs/SECURITY_QA.md: the 20 questions that chief accountants/IT staff often ask, with honest answers.

## Deliverables
- Commit: "docs: align all product and marketing documents with verified capabilities"
```

---

# PHASE D — "RIPE ENOUGH TO GO TO MARKET" CHECKLIST

Paste this checklist at the end; the agent runs `scripts/release_check.sh` (created in A9), which prints a PASS/FAIL table.

| # | Criterion | How to verify | Prompt |
|---|---|---|---|
| 1 | No more silent fallbacks; `/system/modes` reflects reality | grep + test | A5 |
| 2 | Every decision goes through DecisionService, actor from auth | grep + test | A2 |
| 3 | B2B rules run over HTTP with real master data | test_rule_context_http | A1 |
| 4 | ERP payload complete, idempotent, dead-letter | test_erp_payload_http | A3 |
| 5 | API errors follow RFC7807, no internal leakage | test_error_taxonomy | A4 |
| 6 | FE has no fake data; real login; 1 language | grep + Playwright | A7 |
| 7 | Landing separate from the app; claims sourced; consistent contact details | grep docs+web | A8 |
| 8 | Postgres runs for real in docker compose | CI job | A5/A9 |
| 9 | Schema via Alembic; `alembic check` clean | CI | B1 |
| 10 | VAT/discount/promotion/UOM parse correctly on 20 real (anonymized) customer PO files | evals/documents | B2 |
| 11 | Customer B using PO-001 is not blocked; resubmission creates a revision | test | B4 |
| 12 | Customer master + alias by ID | test | B5 |
| 13 | Value-based approval matrix, SoD | test | B6 |
| 14 | ATP and inventory snapshot from the ERP | test | B7 |
| 15 | JSON log has a request_id linked to the audit | test | B8 |
| 16 | Idempotent email intake | test | C1 |
| 17 | OCR/outbox run in the background, multi-process SSE | docker test | C2 |
| 18 | 1 ERP connector confirmed on a real sandbox | contract test | C3 |
| 19 | Zalo/Telegram approvals really work from a manager's phone | PR screenshots | C4 |
| 20 | SKU precision@1 ≥ 95% on the pilot customer's eval set | run_evals | C5 |
| 21 | Playwright 6 journeys + axe clean | CI | C6 |
| 22 | Pilot report can be exported | test | C7 |
| 23 | Documents & deck match capabilities | manual review | C8 |
| 24 | DB backup/restore rehearsed, recorded in the RUNBOOK | rehearsal | B8/A9 |
| 25 | At least 1 distributor has used it for 30 days and agrees to be a case study | in practice | — |

---

## APPENDIX A — END-OF-SESSION REPORT TEMPLATE (the agent must fill it in)

```
## Done
- [file:line] short description

## Verification
- unittest: N tests, 0 failures (duration)
- tsc/lint: clean
- New tests: file name, number of tests, goes through HTTP: yes/no
- Manual check: step 1…, result

## Not done / findings outside the scope
- … (state clearly so the next prompt can be created)

## Risks
- …
```

## APPENDIX B — FINDING CODE NAMING CONVENTION

- NOUN_CONDITION, uppercase, underscore-separated: `PRICE_MISMATCH`, `CONTRACT_PRICE_EXPIRED`, `CUSTOMER_UNRESOLVED`.
- The default severity lives in the registry; a rule may lower it (not raise it) per policy.
- Each code has a title_vi of ≤ 6 words and a description_vi of 1 sentence explaining the consequence and the action required.

## APPENDIX C — LIST OF FINDING CODES AFTER PHASE B

| Code | Severity | Group |
|---|---|---|
| DUPLICATE_PO | error | duplicate |
| DUPLICATE_PENDING (HTTP 409, not a finding) | — | duplicate |
| POSSIBLE_DUPLICATE | warning | duplicate |
| REVISED_ORDER | info | document |
| UNKNOWN_SKU | error / warning (with a suggestion) | catalog |
| INACTIVE_SKU | error (→ warning per policy) | catalog |
| UOM_CONVERSION_MISSING | warning | catalog |
| BELOW_MOQ | warning | catalog |
| INVALID_PACK_SIZE | warning | catalog |
| INVALID_QUANTITY | error | document |
| INVALID_PRICE | error | document |
| TAX_RATE_INVALID | error | document |
| TOTAL_MISMATCH | warning | document |
| PROMO_LINE | info | price |
| PRICE_MISMATCH | warning | price |
| CONTRACT_PRICE_EXPIRED | warning | price |
| DISCOUNT_EXCEEDS_POLICY | warning | price |
| FX_RATE_UNAVAILABLE | error | fx |
| INSUFFICIENT_STOCK | warning | stock |
| INVENTORY_STALE | warning | stock |
| CUSTOMER_BLOCKED | error | credit |
| CUSTOMER_ON_HOLD | warning | credit |
| OVERDUE_DEBT_BLOCKED | error | credit |
| CREDIT_LIMIT_EXCEEDED | error / warning | credit |
| CUSTOMER_UNRESOLVED | error | customer |
| CUSTOMER_FUZZY_MATCHED | warning | customer |
