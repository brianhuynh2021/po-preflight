# BỘ PROMPT KHẮC PHỤC PO PREFLIGHT — TỪ DEMO ĐẾN SẢN PHẨM ĐI CHÀO HÀNG

> Phiên bản 1.0 · 02/09/2026 · Áp dụng cho branch `dev` @ `9103e7a`
> Nguồn: báo cáo soát xét "Soát xét PO Preflight" (8 lỗi tái hiện + ~20 phát hiện đọc code)

---

## PHẦN 0 — CÁCH DÙNG BỘ PROMPT NÀY

### 0.1. Nguyên tắc vận hành

1. **Một prompt = một session = một branch = một PR.** Không gộp. Tên branch ghi sẵn trong từng prompt.
2. **Luôn dán `PROMPT 00 (Bối cảnh chung)` lên đầu** mỗi session trước prompt cụ thể. Prompt 00 chứa quy tắc bất biến của dự án; các prompt sau chỉ tham chiếu, không lặp lại.
3. **Thứ tự bắt buộc:** A1 → A2 → A3 → A4 → A5 → … Các prompt trong cùng giai đoạn có phụ thuộc lẫn nhau; bảng phụ thuộc ở mục 0.3.
4. **Definition of Done cho mọi prompt** (agent phải tự kiểm trước khi báo xong):
   - `PYTHONPATH=src python -m unittest discover -s tests` → 0 fail.
   - `cd apps/web && npx tsc --noEmit && npm run lint` → 0 lỗi.
   - Test mới đi qua **HTTP** (`starlette.testclient`) cho mọi thay đổi ở route; không chỉ test hàm thuần.
   - Không còn `except Exception: pass` mới. Không thêm fallback im lặng.
   - Commit theo Conventional Commits, mô tả bằng tiếng Anh, thân commit liệt kê file chính.
5. **Khi agent gặp mâu thuẫn** giữa prompt và code hiện tại → dừng, báo lại kèm file:line, không tự "sáng tác" hướng khác.

### 0.2. Cách dán prompt

```
[Dán PROMPT 00 — Bối cảnh chung]

---

[Dán PROMPT A1 …]
```

### 0.3. Bảng phụ thuộc

| Prompt | Phụ thuộc | Ước lượng |
|---|---|---|
| A1 RuleContext | — | 0,5 ngày |
| A2 DecisionService | A1 | 1 ngày |
| A3 ERP payload | — | 0,5 ngày |
| A4 Error taxonomy | — | 0,5 ngày |
| A5 Xóa silent fallback | A3, A4 | 1 ngày |
| A6 Catalog schema | A1 | 0,5 ngày |
| A7 FE auth + UI thật | A2, A4, A5 | 2 ngày |
| A8 Landing & claim | — | 0,5 ngày |
| A9 Config/CI/Deploy | A5 | 0,5 ngày |
| B1 Data model v2 + migration | A-all | 3 ngày |
| B2 Line item v2 (VAT/CK/UOM) | B1 | 2 ngày |
| B3 Rules v2 | B2 | 2 ngày |
| B4 Revision & duplicate | B1 | 1,5 ngày |
| B5 Customer master | B1 | 1,5 ngày |
| B6 Users/roles/ma trận duyệt | B1, A2 | 2 ngày |
| B7 Inventory source & ATP | B1, B2 | 2 ngày |
| B8 Observability | A4 | 1 ngày |
| C1 Email intake | B-all | 2 ngày |
| C2 Job queue & Redis | B-all | 2 ngày |
| C3 MISA connector thật | A3, B2 | 3 ngày + sandbox |
| C4 Zalo OA thật | A2, B6 | 2 ngày |
| C5 Embedding thật & eval | B5 | 2 ngày |
| C6 FE pilot-ready | A7, B-all | 3 ngày |
| C7 Pilot metrics | B8 | 1 ngày |
| C8 Marketing trung thực | C7 | 1 ngày |

---

## PROMPT 00 — BỐI CẢNH CHUNG (DÁN ĐẦU MỌI SESSION)

```
Bạn đang làm việc trên repo PO Preflight (github.com/brianhuynh2021/po-preflight, branch dev).

## Dự án là gì
Cổng tiền kiểm đơn đặt hàng (PO) B2B cho nhà phân phối Việt Nam: nhận file PO (JSON/CSV/TXT/PDF/Excel/ảnh),
bóc tách, khớp SKU, chạy luật xác định (giá, tồn, trùng, công nợ, UOM), người có thẩm quyền duyệt
(Web/Telegram/Zalo), rồi mới đẩy vào ERP qua Transactional Outbox.

## Stack
- Backend: Python 3.11+, FastAPI, Pydantic v2, SQLite (dev) / PostgreSQL (prod), LangGraph, RapidFuzz.
  Mã nguồn tại src/preflight/. Test: tests/*.py dùng unittest + starlette.testclient.
  Chạy test: PYTHONPATH=src python -m unittest discover -s tests
- Frontend: Next.js 16 (qua vinext/Vite), React 19, TypeScript strict, CSS custom properties trong
  apps/web/app/globals.css (token M3). SDK gọi API: apps/web/app/lib/api/client.ts.
  Domain types: apps/web/app/lib/types.ts, logic dẫn xuất: apps/web/app/lib/derive.ts.
  Chạy kiểm tra: cd apps/web && npx tsc --noEmit && npm run lint
- Kiến trúc module: parsers.py → rules.py (hàm thuần) → store.py (BaseAuditStore ABC) →
  api/routes/*.py; agent/ (LangGraph), rag/ (4-tier SKU matcher), erp/ (outbox + adapters),
  bot/ (telegram, zalo), security/ (rbac, rate_limiter, audit_chain), ingestion/ (OCR, excel).

## QUY TẮC BẤT BIẾN (vi phạm = PR bị từ chối)
1. KHÔNG fallback im lặng. Mọi đường rẽ nhánh sang mock/dry-run/offline phải:
   (a) chỉ bật bằng cờ tường minh (biến môi trường hoặc tham số test),
   (b) để lại dấu vết người dùng thấy được: field `mode` trong response API
       (giá trị: "live" | "dry_run" | "mock" | "offline") và badge trên UI,
   (c) ghi log WARNING có lý do gốc.
   Trong production (PREFLIGHT_ENV=production) mọi fallback đều bị cấm → fail fast.
2. KHÔNG `except Exception: pass`. Bắt exception cụ thể; nếu phải bắt rộng thì log
   `logger.exception(...)` và trả lỗi có mã.
3. Mọi quyết định (approve/reject/needs_changes) từ MỌI kênh đi qua đúng một hàm
   `preflight.services.decisions.decide_order(...)`. Không kênh nào gọi thẳng store.record_decision.
4. Actor của mọi hành động lấy từ principal đã xác thực phía server, không nhận từ payload.
5. Rule engine (rules.py) phải là hàm thuần: không I/O, không mạng, không đọc env. Mọi dữ liệu
   đầu vào đi qua RuleContext.
6. Mọi thay đổi route phải có test đi qua HTTP (TestClient), không chỉ test hàm.
7. UI khách hàng dùng MỘT ngôn ngữ: tiếng Việt. Không có số issue GitHub, tên biến kỹ thuật,
   hay số liệu hardcode trong UI. Số liệu không có từ API → hiển thị "—" kèm lý do, không bịa.
8. Không thêm claim marketing (100%, Zero-Hallucination, SOX, SOC2…) vào code/README/UI.
9. Tiền: backend dùng Decimal; FE dùng number nhưng luôn format qua money(value, currency),
   không bao giờ hardcode "$" hay "đ".
10. Migration: mọi thay đổi schema DB đi qua migration file trong src/preflight/migrations/,
    không sửa trực tiếp chuỗi SCHEMA (sau khi B1 hoàn tất).

## Cách làm việc
- Đọc kỹ file liên quan trước khi sửa. Trích dẫn file:line khi báo cáo.
- Viết test trước cho hành vi mới, chạy để thấy fail, rồi sửa.
- Khi xong: chạy đủ 3 lệnh kiểm tra ở trên, liệt kê file đã đổi, mô tả cách kiểm chứng tay.
- Nếu prompt mâu thuẫn với code hiện tại hoặc thiếu thông tin: DỪNG và hỏi, kèm file:line.
```

---

# GIAI ĐOẠN A — P0: LÀM CHO CÁI ĐÃ CÓ CHẠY THẬT

Mục tiêu giai đoạn: sau A9, mọi tính năng hiện diện trên UI/API đều **chạy thật hoặc nói rõ là không**. Không thêm nghiệp vụ mới.

---

## PROMPT A1 — RuleContext: nối master data và policy vào rule engine

**Branch:** `fix/a1-rule-context`

```
## Mục tiêu
Các luật B2B (giá hợp đồng, công nợ, UOM/MOQ) và chính sách price tolerance hiện KHÔNG BAO GIỜ
được áp dụng khi phân tích đơn qua API hay agent, dù rules.py đã hỗ trợ. Sửa bằng cách tạo một
đối tượng RuleContext duy nhất, xây ở một chỗ, và truyền vào analyze_order ở cả 3 điểm gọi.

## Bằng chứng
- src/preflight/api/routes/orders.py:236   analyze_order(order, catalog, duplicate=duplicate)
- src/preflight/api/routes/orders.py:300   analyze_order(updated_order, catalog, duplicate=False)
- src/preflight/agent/nodes.py:120         analyze_order(order, catalog, duplicate=duplicate)
- src/preflight/api/routes/rules.py:13     _POLICY_STATE in-memory, không ai đọc ngoài GET/PUT
- Tái hiện: set /customers/{id}/credit status=BLOCKED → upload PO → ready_for_approval, 0 finding.

## Yêu cầu
1. Tạo src/preflight/rules_context.py:
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
   - build_rule_context là NƠI DUY NHẤT gọi store.get_customer_pricing / get_uom_conversions /
     get_customer_credit / has_po, và gọi fx_provider cho các cặp tiền tệ xuất hiện trong order.
   - Lookup khách hàng: tạm thời dùng chuỗi tên như hiện tại nhưng chuẩn hóa qua một hàm
     `normalize_customer_key(name)` (strip, upper, bỏ dấu, bỏ tiền tố "CÔNG TY", "CTY", "CÔNG TY CỔ PHẦN",
     "CT CP", "TNHH", "MTV", dấu chấm phẩy). Ghi rõ TODO(B5) rằng sẽ thay bằng customer_id.
2. Đổi chữ ký:
   `analyze_order(order: Order, ctx: RuleContext) -> Analysis`
   Giữ hàm cũ dưới tên `analyze_order_legacy(...)` gọi vào hàm mới, đánh dấu deprecated, để test cũ
   không vỡ ngay; xóa ở cuối prompt sau khi đã cập nhật hết test.
3. rules.py phải trở thành hàm thuần: xóa `from preflight.currency import fx_engine`; dùng
   ctx.fx_rates. Nếu thiếu tỷ giá cho cặp tiền → thêm Finding code="FX_RATE_UNAVAILABLE"
   severity="error" (không đoán tỷ giá).
4. Policy: tạo model Pydantic RulePolicy (price_tolerance_percent: Decimal, stock_safety_margin: int,
   allow_inactive_sku: bool, auto_approve_ready: bool). Persist vào bảng mới `rule_policies`
   (id=1 singleton, json, updated_at, updated_by). Thêm store.get_policy()/set_policy() vào
   BaseAuditStore, cả SQLite và Postgres. routes/rules.py đọc/ghi qua store; xóa _POLICY_STATE.
   (Tạm thời sửa trực tiếp chuỗi SCHEMA vì migration runner chưa có — ghi TODO(B1).)
5. Áp dụng stock_safety_margin: INSUFFICIENT_STOCK khi base_quantity > stock - safety_margin.
   Áp dụng allow_inactive_sku: nếu True, INACTIVE_SKU hạ từ error xuống warning.
6. Cập nhật 3 điểm gọi (orders.py x2, nodes.py) dùng build_rule_context + analyze_order mới.
   Cả upload, confirm-extraction và agent phải cho cùng kết quả với cùng đầu vào.
7. currency.py: DynamicFXEngine giữ lại nhưng chỉ được gọi từ build_rule_context qua fx_provider;
   thêm cờ PREFLIGHT_FX_LIVE (mặc định false). Khi false → chỉ dùng FALLBACK_RATES và đánh dấu
   ctx.fx_rates nguồn "static". Ghi nguồn tỷ giá vào message PRICE_MISMATCH.

## Không được làm
- Không sửa nội dung message các finding hiện có ngoài phần nguồn tỷ giá (FE đang map theo code).
- Không đổi tên/thêm finding code ngoài FX_RATE_UNAVAILABLE.

## Tiêu chí chấp nhận (viết test trước)
tests/test_rule_context_http.py, đi qua TestClient với DB tạm và dependency_overrides:
  a) set credit BLOCKED → upload → status "blocked", có CUSTOMER_BLOCKED.
  b) set contract price 17.000.000 cho LAPTOP-A14 → upload giá 17.000.000 → không PRICE_MISMATCH.
  c) PUT /rules tolerance=10 → upload lệch 2,7% → không PRICE_MISMATCH; tolerance=0 → có.
  d) set uom CARTON=20 PCS cho CAB-CAT6-3M → upload qty 2 CARTON → so tồn theo 40 PCS.
  e) restart store (đóng/mở lại) → policy vẫn còn (persist).
  f) POST /agent/run với cùng dữ liệu (a) → risk_level HIGH, finding CUSTOMER_BLOCKED.
  g) đơn USD khi PREFLIGHT_FX_LIVE=false → PRICE_MISMATCH message chứa "tỷ giá tĩnh".
Test cũ: cập nhật sang chữ ký mới; xóa analyze_order_legacy khi không còn ai gọi.

## Bàn giao
- Files: rules_context.py (mới), rules.py, routes/orders.py, routes/rules.py, agent/nodes.py,
  store.py (policy), currency.py, tests mới.
- Commit: "fix(rules): introduce RuleContext and wire B2B master data, policy and FX into all analyze paths"
```

---

## PROMPT A2 — DecisionService: một cửa cho mọi quyết định, actor từ auth

**Branch:** `fix/a2-decision-service`

```
## Mục tiêu
Hiện có 3 đường ghi quyết định khác nhau: route /decide (có governance), Telegram webhook và Zalo
webhook (gọi thẳng store.record_decision, KHÔNG governance, KHÔNG auth), agent human_approval_node
(chỉ đổi state). Hậu quả đã tái hiện: đơn Blocked được duyệt qua Telegram bởi payload tự khai.
Ngoài ra actor trong /decide do client gửi (đã tái hiện "CEO_Nguyen_Van_A").

## Bằng chứng
- src/preflight/bot/telegram.py:220-245   record_decision trực tiếp
- src/preflight/bot/zalo.py:196-203        record_decision trực tiếp
- src/preflight/api/routes/orders.py:317   payload.actor được dùng làm actor
- src/preflight/api/schemas.py:161         DecisionRequest.actor: str
- src/preflight/api/routes/bot.py:77-95    webhook không yêu cầu secret ở dev

## Yêu cầu
1. Tạo src/preflight/services/__init__.py và src/preflight/services/decisions.py:
   ```python
   @dataclass(frozen=True)
   class Principal:
       user_id: str; display_name: str; role: Role; channel: Literal["web","telegram","zalo","api","agent"]

   @dataclass(frozen=True)
   class DecisionResult:
       decision_id: int; po_number: str; decision: str; actor: str; note: str; created_at: str
       previous_status: str; new_status: str

   class DecisionError(Exception):  # mang status_code + code + message
       ...

   def decide_order(store: BaseAuditStore, *, order_ref: str | int, decision: str, note: str,
                    principal: Principal, event_bus: EventBus | None = None) -> DecisionResult:
       # 1. load order (404 nếu không có)
       # 2. RBAC: principal.role >= MANAGER (403)
       # 3. validate_order_decision(current_status, decision, note, error_count) (409/422)
       # 4. store.record_decision(po, decision, actor=f"{principal.channel}:{principal.user_id}",
       #                          note, display_name=principal.display_name)
       # 5. publish "order.decided" với actor, channel
       # 6. return DecisionResult
   ```
2. routes/orders.py /decide: xóa actor khỏi DecisionRequest (giữ tương thích: nếu client gửi
   actor → bỏ qua và trả header `X-Deprecated-Field: actor`). Principal dựng từ UserPrincipal
   (rbac.get_current_user), channel="web" nếu có header X-Client: web, else "api".
3. Telegram:
   - Tạo bảng `channel_identities(channel, external_id, user_id, display_name, role, created_at)`
     UNIQUE(channel, external_id). Thêm store.get_channel_identity()/upsert_channel_identity().
   - handle_callback_action nhận from_user.id (không phải username), tra channel_identities;
     không có → trả popup "Tài khoản Telegram chưa được liên kết. Liên hệ quản trị." và KHÔNG ghi gì.
   - Có → gọi decide_order. DecisionError → popup message tiếng Việt tương ứng
     (409 blocked: "Đơn đang bị chặn, không thể duyệt."; 422: "Cần ghi chú ≥10 ký tự — hãy duyệt trên web.").
   - Sau quyết định thành công: gọi editMessageReplyMarkup để vô hiệu nút (tránh bấm 2 lần).
   - Webhook: BẮT BUỘC TELEGRAM_WEBHOOK_SECRET ở mọi môi trường; thiếu → 503 kể cả dev.
   - Endpoint admin: POST /api/v1/bot/telegram/link {telegram_user_id, user_id, role} (ADMIN).
4. Zalo: tương tự — process_webhook_event lấy sender.id, tra channel_identities, gọi decide_order.
   verify_webhook_signature: khi không có secret_key → return False (không còn "dev mode True").
5. Agent human_approval_node: nhận state["decision"], state["decided_by"] (là user_id nội bộ),
   gọi decide_order với channel="agent"; nếu DecisionError → set state["status"]="decision_rejected",
   state["error"]=message, KHÔNG sang erp_sync. Cập nhật route_after_human_approval.
6. Bỏ mọi chỗ khác gọi store.record_decision ngoài services/decisions.py. Thêm test tĩnh:
   grep trong src/ không có "record_decision(" ngoài store.py và services/decisions.py.
7. record_decision trong store: thêm cột `display_name`, `channel` vào decisions (sửa SCHEMA,
   TODO(B1)); audit block payload gồm cả channel.

## Tiêu chí chấp nhận
tests/test_decision_service_http.py:
  a) POST /decide với body có "actor":"X" → response actor là username của API key, không phải X.
  b) Telegram webhook approve đơn blocked (đã link identity MANAGER) → 200 nhưng result.success=False,
     popup chứa "bị chặn"; order vẫn blocked.
  c) Telegram webhook từ user chưa link → không ghi decision; popup "chưa được liên kết".
  d) Telegram webhook thiếu header secret → 403; server thiếu TELEGRAM_WEBHOOK_SECRET → 503 kể cả dev.
  e) Zalo webhook không chữ ký → 401; có chữ ký đúng + identity VIEWER → 403 (không đủ role).
  f) Agent resume với decision APPROVED trên đơn blocked → status decision_rejected, erp_synced False.
  g) Approve lần 2 cùng đơn → 409.
  h) grep test: không còn record_decision ngoài 2 file cho phép.

## Bàn giao
- Commit: "fix(security): route all channel decisions through DecisionService with authenticated actor and governance"
```

---

## PROMPT A3 — ERP payload đúng dữ liệu, adapter chọn theo cấu hình, không giả thành công

**Branch:** `fix/a3-erp-payload`

```
## Mục tiêu
Outbox hiện nhận items=[] (route ERP đọc sai key) và agent gửi items=[] total=0 (đọc key không
tồn tại trong state). Adapter live trả success=True ở dry-run mà không phân biệt. Sửa để payload
ERP luôn là bản sao đầy đủ của đơn đã duyệt và chế độ chạy luôn hiển hiện.

## Bằng chứng
- src/preflight/api/routes/erp.py:48-50    order.get("line_items") or order.get("items", []) — row chỉ có order_json
- src/preflight/agent/nodes.py:232-238     state.get("items"), state.get("total"), state.get("currency") — không có trong PreflightAgentState
- src/preflight/erp/adapters/odoo_live.py:31  dry_run → success=True không dấu vết
- Tái hiện: outbox payload items: [] total_amount: 18000000.0 (API) / 0.0 (agent)

## Yêu cầu
1. Tạo src/preflight/erp/payload.py:
   ```python
   def build_erp_payload(order_row: dict[str, Any] | Order, *, decision: DecisionResult | None) -> ERPOrderDraft
   ```
   - Nhận row từ store (parse order_json) HOẶC domain Order; trả dataclass gồm po_number, customer,
     currency, items (sku, description, quantity, uom, unit_price, line_total), subtotal, approved_by,
     approved_at, source_analysis_id. Raise ValueError nếu items rỗng hoặc tổng ≠ Σ line_total.
2. routes/erp.py /sync/{order_id}: chỉ cho phép khi order.latest_decision == "approved" (409 nếu
   không). Dùng build_erp_payload. Xóa nhánh "If already sent previously, return idempotent success"
   tự chế transaction_id "ERP-SO-{po}"; thay bằng đọc lại outbox theo idempotency_key và trả bản ghi thật.
3. agent/nodes.py erp_sync_node: dùng state["order"] (đã có từ audit_rules_node) qua build_erp_payload;
   xóa mọi state.get("items"/"total"/"currency").
4. Idempotency key: hiện = sha256(po:customer:total)[:24]. Đổi thành sha256(analysis_id:po:revision_hash)
   trong đó revision_hash = sha256 của items chuẩn hóa. Lý do: cùng PO cùng tổng nhưng khác dòng phải
   là event khác.
5. Chọn adapter: tạo erp/registry.py với get_adapter(name: str | None) đọc ERP_DEFAULT_ADAPTER
   (MOCK_SAP|MOCK_ODOO|ODOO_LIVE|SAP_LIVE|MISA_AMIS_LIVE). Route nhận adapter_type tùy chọn nhưng
   chỉ ADMIN mới được override. Agent dùng get_adapter(None).
6. ERPSyncResponse thêm field `mode: Literal["live","dry_run","mock"]`. Mọi adapter set đúng mode.
   Live adapter thiếu credential:
   - PREFLIGHT_ENV=production → raise ERPConfigurationError → outbox mark_failed với lý do,
     KHÔNG success.
   - dev → mode="dry_run", transaction_id tiền tố "DRYRUN-", log WARNING.
7. Outbox: thêm trạng thái PROCESSING thật (fetch_pending đánh dấu PROCESSING trong cùng transaction,
   tránh 2 worker xử lý trùng); retry backoff (retry_count → delay 1m/5m/30m, cột next_attempt_at);
   sau 3 lần → DEAD_LETTER (trạng thái mới), không lẫn với FAILED.
8. Worker ghi metrics_registry.record_erp_sync(adapter, success) (hiện có hàm nhưng không ai gọi).

## Tiêu chí chấp nhận
tests/test_erp_payload_http.py:
  a) upload PO 3 dòng → approve (qua /decide với note hợp lệ) → /erp/sync → outbox payload_json
     có đúng 3 items, subtotal = tổng đơn, currency đúng.
  b) /erp/sync trên đơn chưa approve → 409.
  c) Agent run đơn sạch (LOW) → erp_synced True và outbox items khớp line_items đầu vào.
  d) Sync 2 lần cùng đơn → 1 event trong outbox, lần 2 trả bản ghi cũ (mode, transaction_id giống).
  e) ODOO_LIVE không credential + PREFLIGHT_ENV=production → event FAILED, response success=False,
     error_message chứa "credential".
  f) dev → mode="dry_run", transaction_id bắt đầu "DRYRUN-".
  g) mark_failed 3 lần → status DEAD_LETTER; fetch_pending không trả về nữa.

## Bàn giao
- Commit: "fix(erp): build full ERP payload from persisted order, honest sync modes, outbox processing/dead-letter"
```

---

## PROMPT A4 — Error taxonomy: lỗi có mã, không nuốt, không lộ nội bộ

**Branch:** `fix/a4-error-taxonomy`

```
## Mục tiêu
Upload route bao `except Exception` → mọi lỗi (413, 404, NameError, IntegrityError) thành
400 "Failed to process PO file: <str(exc)>". `status` chưa import gây NameError khi file >10MB.
Chuẩn hóa toàn bộ lỗi API theo RFC 7807 Problem Details, có mã máy đọc để FE hiển thị đúng.

## Bằng chứng
- src/preflight/api/routes/orders.py:200   status.HTTP_413_… nhưng không import status
- src/preflight/api/routes/orders.py:246-248  except Exception → 400 + str(exc)
- Tái hiện: upload 11MB → 400 "name 'status' is not defined"

## Yêu cầu
1. Tạo src/preflight/api/errors.py:
   ```python
   class PreflightError(Exception):
       status_code: int; code: str; message_vi: str; detail: dict | None
   # Con: ParseError(400,"PARSE_ERROR"), UnsupportedFormat(415,"UNSUPPORTED_FORMAT"),
   #      PayloadTooLarge(413,"PAYLOAD_TOO_LARGE"), NotFound(404,"NOT_FOUND"),
   #      DecisionConflict(409,"DECISION_CONFLICT"), ValidationFailed(422,"VALIDATION_FAILED"),
   #      Forbidden(403,"FORBIDDEN"), Unauthorized(401,"UNAUTHORIZED"),
   #      UpstreamUnavailable(503,"UPSTREAM_UNAVAILABLE"), ConfigurationError(500,"CONFIGURATION_ERROR")
   ```
   Exception handler đăng ký trên app trả JSON:
   {"type":"https://popreflight.vn/errors/<code>","title":..., "status":..., "code":..., "detail": message_vi,
    "request_id": <X-Request-ID>, "errors": [...] (tùy chọn)}
   Content-Type: application/problem+json.
2. Handler cho RequestValidationError (Pydantic) → 422 code "VALIDATION_FAILED", errors = danh sách
   {field, message} đã dịch tiếng Việt cơ bản (required, type, min_length).
3. Handler cho Exception không lường trước → 500 code "INTERNAL_ERROR", detail cố định
   "Lỗi hệ thống. Mã tham chiếu: {request_id}". logger.exception với request_id. KHÔNG bao giờ trả str(exc).
4. routes/orders.py upload: import status; tách try: chỉ bao parse_order → ParseError; kiểm size
   trước khi ghi file; HTTPException/PreflightError không bị bắt lại. Xóa file tạm khi parse lỗi.
   Ghi file upload theo <analysis_id>/<safe_name> sau khi có id (hiện tên ngẫu nhiên không truy ngược).
   Lưu đường dẫn vào cột analyses.source_path (SCHEMA, TODO(B1)).
5. Toàn bộ route khác: thay HTTPException(detail=str) bằng PreflightError tương ứng; giữ mã HTTP cũ.
6. rbac.py: 401/403 qua Unauthorized/Forbidden để thống nhất format.
7. Rate limiter: 429 cũng theo format problem+json, code "RATE_LIMITED", có Retry-After.
8. FE SDK (client.ts): ApiError parse problem+json → có .code, .requestId, .detailVi; export
   hàm `describeError(err): string` trả tiếng Việt. (UI dùng ở A7.)

## Tiêu chí chấp nhận
tests/test_error_taxonomy.py:
  a) upload 11MB → 413, body.code == "PAYLOAD_TOO_LARGE", có request_id, không chứa "NameError".
  b) upload .docx → 415 UNSUPPORTED_FORMAT.
  c) upload JSON thiếu po_number → 400 PARSE_ERROR, detail tiếng Việt, không chứa traceback.
  d) GET /orders/999999 → 404 NOT_FOUND format problem+json.
  e) decide thiếu note → 422 VALIDATION_FAILED hoặc DECISION_CONFLICT đúng ngữ cảnh.
  f) gây lỗi nội bộ giả (monkeypatch store.get_order raise RuntimeError("secret-db-path")) →
     500 INTERNAL_ERROR, body KHÔNG chứa "secret-db-path".
  g) Không còn file rác trong runtime/uploads sau upload lỗi.

## Bàn giao
- Commit: "fix(api): RFC7807 problem details, typed errors, no exception leakage, upload size guard"
```

---

## PROMPT A5 — Xóa mọi fallback im lặng

**Branch:** `fix/a5-no-silent-fallback`

```
## Mục tiêu
Hệ thống hiện "xanh" ở mọi tầng dù không gì chạy thật: Postgres→SQLite, Gemini→đơn hàng bịa,
Telegram/Zalo→success=True, ERP→dry-run success, FE→seed data. Làm cho mỗi chỗ hoặc chạy thật,
hoặc thất bại rõ, hoặc dán nhãn chế độ.

## Bằng chứng
- src/preflight/store.py:825-838            Postgres lỗi → AuditStore("runtime/pg_fallback.db")
- src/preflight/erp/outbox.py:283-297       tương tự
- src/preflight/ingestion/ocr_engine.py:64-71, 150-194   mock trả đơn "Northstar Scanned Ingestion" conf 0.92
- src/preflight/ingestion/pipeline.py:41,92 except Exception: pass
- src/preflight/bot/telegram.py:127-137     dry-run success=True message_id "mock_msg_12345"
- pyproject.toml không có psycopg; Dockerfile không cài → Postgres chưa từng chạy trong container

## Yêu cầu
1. Postgres:
   - Thêm dependency `psycopg[binary,pool]>=3.1` (psycopg 3, không phải psycopg2) vào pyproject
     [project.dependencies]. Cập nhật PostgresAuditStore/PostgresOutboxStore sang psycopg3
     ConnectionPool. Xóa hoàn toàn _fallback_sqlite. Lỗi kết nối → raise ConfigurationError
     lúc startup (lifespan) → process thoát với log rõ.
   - /health/ready trả 503 nếu DB không truy vấn được; body ghi backend thật ("postgresql"/"sqlite")
     thay vì hardcode "sqlite" (routes/health.py:52).
   - tests/test_database_dual_backend.py: phần Postgres chỉ chạy khi có biến TEST_DATABASE_URL,
     ngược lại skipTest với lý do rõ — không được pass giả trên fallback.
2. OCR:
   - GeminiVisionOCREngine.extract: thiếu api_key → raise UpstreamUnavailable("OCR chưa cấu hình").
     Gọi Gemini lỗi → raise UpstreamUnavailable kèm lý do, đi qua vision_ai_circuit_breaker
     (hiện có nhưng không dùng — resilience/circuit_breaker.py).
   - Mock extractor chuyển sang tests/fixtures/mock_ocr.py, chỉ inject qua tham số engine trong test.
     Xóa _mock_vision_extraction khỏi src.
   - Pipeline: bỏ 2 `except Exception: pass`; lỗi Excel → raise ParseError với sheet/row nếu có;
     lỗi parser text → thử OCR CHỈ khi doc_type là SCANNED_PDF/IMAGE_RASTER, không phải cho JSON/CSV
     hỏng. ExtractedOrder thêm field `mode` và `extractor_used` đã có → đảm bảo trung thực.
   - Route /ingest/extract: khi OCR không khả dụng → 503 UPSTREAM_UNAVAILABLE với hướng dẫn
     "Tải lên Excel/CSV hoặc nhập tay tại Staging".
3. Bot:
   - BotNotificationResult thêm `mode`. Thiếu token → mode="dry_run", success=True CHỈ khi
     TELEGRAM_DRY_RUN=true tường minh; nếu không → success=False, details "Telegram chưa cấu hình".
     Production + chưa cấu hình → không gửi, ghi audit block "NOTIFY_SKIPPED".
   - message_id giả "mock_msg_12345"/"zalo_msg_simulated_9988" → None khi dry-run.
4. ERP: đã xử lý ở A3; kiểm tra lại mọi adapter đều set mode.
5. LangGraph checkpointer: MemorySaver → nếu DATABASE_URL là postgres dùng langgraph-checkpoint-postgres,
   nếu sqlite dùng langgraph-checkpoint-sqlite (file runtime/agent_checkpoints.db). Thêm dependencies.
   Không còn _SERVER_CHECKPOINTER in-memory.
6. Thêm endpoint GET /api/v1/system/modes (VIEWER) trả:
   {"database":"postgresql|sqlite","ocr":"live|unavailable","telegram":"live|dry_run|unconfigured",
    "zalo":..., "erp":{"adapter":"...", "mode":"live|dry_run|mock"}, "fx":"live|static",
    "environment": PREFLIGHT_ENV, "auth_required": bool}
   FE sẽ dùng để hiển thị banner (A7). /metrics: xóa hardcode version/environment; đọc từ
   preflight.__version__ và PREFLIGHT_ENV.
7. Dockerfile: cài `.[pdf]` và psycopg; pin Python 3.12 (khớp CI); healthcheck dùng /health/ready.
   docker-compose: thêm service postgres (postgres:16), backend DATABASE_URL trỏ vào; profile
   `sqlite` cho dev nhẹ.

## Tiêu chí chấp nhận
  a) DATABASE_URL=postgresql://sai → app startup raise, không tạo runtime/pg_fallback.db.
  b) /ingest/extract ảnh PNG khi không GEMINI_API_KEY → 503 UPSTREAM_UNAVAILABLE; không có bản ghi
     "Northstar Scanned Ingestion" trong DB. grep src/ không còn "Northstar Scanned".
  c) telegram/notify không token, không TELEGRAM_DRY_RUN → success=False mode="unconfigured".
  d) GET /system/modes phản ánh đúng env trong test (đặt env khác nhau qua monkeypatch).
  e) /agent/run rồi khởi tạo graph mới (mô phỏng restart) → /agent/state/{thread} vẫn tìm thấy.
  f) grep src/ không còn "except Exception:\n *pass".
  g) docker compose up (sqlite profile) → /health/ready 200; (postgres profile) → database=postgresql.

## Bàn giao
- Commit: "fix(core): remove silent fallbacks (db, ocr, bots, checkpointer); expose system modes; real Postgres support"
```

---

## PROMPT A6 — Catalog schema đầy đủ: moq, pack_size, base_uom; parser giữ UOM

**Branch:** `fix/a6-catalog-schema`

```
## Mục tiêu
Luật MOQ/pack/UOM chỉ sống trong unit test vì load_catalog chỉ đọc 5 cột và parser bỏ uom dòng hàng.

## Bằng chứng
- src/preflight/catalog.py:13-20      chỉ sku,name,unit_price,stock,active
- src/preflight/parsers.py:42-47      LineItem không nhận uom
- examples/catalog.csv                không có cột
- Tái hiện: get_catalog()["LAPTOP-A14"].moq == 1 (mặc định)

## Yêu cầu
1. catalog.py: đọc thêm cột tùy chọn `base_uom` (mặc định PCS), `moq` (int ≥1), `pack_size` (int ≥1),
   `category`, `barcode`. Thiếu cột → mặc định; giá trị sai kiểu → raise ValueError kèm số dòng.
   Đường dẫn catalog đọc từ env CATALOG_PATH (deps.py hiện hardcode). Cache catalog theo mtime file
   (hiện parse CSV mỗi request).
2. Product thêm `category: str | None`, `barcode: str | None`.
3. parsers.py: JSON/CSV/TXT nhận `uom` (mặc định PCS); TXT format cho phép 4 cột
   `SKU | QTY | UOM | UNIT_PRICE` và vẫn nhận 3 cột cũ. Excel extractor đã đọc uom → giữ.
4. examples/catalog.csv: thêm cột với dữ liệu hợp lý; thêm examples/orders/po-carton.json dùng
   uom CARTON cần conversion.
5. API /catalog: trả các cột mới. Thêm POST /api/v1/catalog/import (ADMIN, multipart CSV): validate
   toàn bộ trước, báo lỗi theo dòng (422 VALIDATION_FAILED, errors=[{row, column, message}]),
   thành công thì ghi file mới + lưu bản cũ với timestamp (không silent overwrite — PRD FR-054),
   ghi audit block "CATALOG_IMPORTED".
6. UI Catalog (apps/web/components/catalog/CatalogView.tsx): hiển thị base_uom, MOQ, pack size;
   nút "Nhập catalog CSV" gọi endpoint mới, hiển thị lỗi theo dòng.
7. FE types: Product thêm baseUom, moq, packSize.

## Tiêu chí chấp nhận
  a) catalog mới → moq/pack đúng; catalog cũ 5 cột vẫn load được.
  b) upload po-carton.json + uom conversion → INSUFFICIENT_STOCK tính theo PCS; không conversion →
     finding UOM_CONVERSION_MISSING (warning, thêm code mới này, cập nhật FE FINDING_TITLE).
  c) qty 3 với pack_size 5 → INVALID_PACK_SIZE qua HTTP.
  d) import CSV có dòng lỗi → 422 với row/column; file cũ không đổi.
  e) sửa file catalog trên đĩa → request kế tiếp thấy dữ liệu mới (cache theo mtime).

## Bàn giao
- Commit: "feat(catalog): full product schema (uom/moq/pack), CSV import with validation, parsers keep UOM"
```

---

## PROMPT A7 — Frontend: đăng nhập thật, dữ liệu thật, một ngôn ngữ, quyết định đủ

**Branch:** `fix/a7-frontend-truth`

```
## Mục tiêu
FE hiện không gửi xác thực (mọi POST 401), bắt lỗi rồi giả thành công, đầy số liệu hardcode,
lẫn Anh–Việt, thiếu nút Từ chối, ghi chú không đủ 10 ký tự, "$" cho đơn VND, và tiêu đề có số issue.

## Bằng chứng
- apps/web/app/lib/api/client.ts:44-52           không header auth
- apps/web/components/orders/OrdersView.tsx:72-79  catch → status Approved local + toast "was approved"
- OrdersView.tsx:227-247   "Average decision time 6m", "42", spark cứng
- OrdersView.tsx:470-478   `$${line.unitPrice.toFixed(2)}`
- overview/OverviewView.tsx:20-60   "GOOD MORNING, MAYA", "Two orders need attention", 86%, +18%
- layout/Sidebar.tsx:85,161  Northwind Co., Maya Chen; :149 "Processing is healthy" cứng
- settings/SettingsView.tsx:45  "(ISSUE #8 & #43)"; staging/ExtractionReviewStudio.tsx:33 "(Issue #38)"
- orders/DecisionModal.tsx:59  disabled chỉ khi note rỗng (backend cần ≥10)
- AppStateProvider.tsx: isLiveConnected tính nhưng không hiển thị

## Yêu cầu
### 1. Xác thực
- Backend: thêm POST /api/v1/auth/login {api_key} → set cookie HttpOnly `pf_session` (JWT HS256,
  exp 8h, secret PREFLIGHT_SESSION_SECRET bắt buộc ở production) và trả {user, role}.
  GET /api/v1/auth/me, POST /api/v1/auth/logout. rbac.get_current_user chấp nhận cookie hoặc header.
  CORS allow_credentials=True với origin cụ thể (đã có).
- FE: trang /login (ngoài app shell), form nhập API key (tạm, cho tới B6 có user/password).
  Middleware Next: chưa có cookie → redirect /login. client.ts: fetch với credentials:"include";
  401 → clear và chuyển /login.
- Hiển thị user thật trong Sidebar (từ /auth/me), xóa "Maya Chen"/"Northwind Co."; workspace name
  đọc từ GET /api/v1/system/modes (thêm field company_name từ env PREFLIGHT_COMPANY_NAME).

### 2. Không giả thành công
- Xóa toàn bộ `catch {}` che lỗi trong OrdersView, CatalogView, SettingsView. Lỗi → toast đỏ với
  describeError(err) (A4). Thành công → chỉ sau khi await thành công và refreshOrders().
- Xóa seedOrders làm state khởi tạo. Trước khi API trả → skeleton; API lỗi → EmptyState
  "Không kết nối được máy chủ (mã lỗi …)" + nút thử lại. seed.ts chỉ còn dùng cho Storybook/test,
  chuyển sang apps/web/tests/fixtures/.
- Banner chế độ: đọc /system/modes; nếu bất kỳ mục là dry_run/mock/unavailable → banner vàng
  đầu trang "Hệ thống đang chạy chế độ thử: OCR chưa cấu hình, Telegram dry-run…". Production
  không có gì thì không hiện.
- Sidebar "Processing is healthy" → đọc /health/ready định kỳ 30s: "Hệ thống ổn định" / "Mất kết nối".

### 3. Số liệu thật
- OrdersMetrics và Overview: dùng GET /api/v1/dashboard/stats; bổ sung backend:
  approved_today, avg_decision_minutes (từ decisions.created_at − analyses.created_at),
  orders_last_7_days (mảng 7 số), straight_through_rate (ready_for_approval / total).
  Không có dữ liệu → "—". Xóa 86%, +18%, 42, 6m, sparkline cứng.
- Overview headline sinh từ dữ liệu: "{n} đơn cần xử lý" (n=0 → "Không có đơn cần xử lý").
  Xóa "GOOD MORNING, MAYA", "2:00 PM cut-off".

### 4. Quyết định
- DecisionModal: 3 hành động Duyệt / Yêu cầu sửa / Từ chối trong một modal có radio; validateNote
  từ derive.ts (MIN_NOTE_LENGTH=10) chặn nút và hiện đếm ký tự; hiển thị lý do khi hành động bị
  khóa (decisionBlockedReason). Bỏ dòng "attributed to Maya Chen" → tên user thật.
- OrdersView: Request changes cũng mở modal (hiện gửi note cứng không qua người dùng).
- Sau quyết định: activity/timeline lấy từ detail.decisions (đã có), xóa initialActivity giả
  ("Olivia Park").

### 5. Ngôn ngữ & copy
- Toàn bộ chrome sang tiếng Việt: "Đơn đặt hàng", "Cần xử lý", "Sẵn sàng duyệt", "Đã duyệt",
  "Tải lên PO", "Phát hiện kiểm tra", "Dòng hàng chuẩn hóa", "Lịch sử", "Yêu cầu sửa", "Xem xét & duyệt".
  Giữ mã trạng thái nội bộ (OrderStatus) nhưng thêm STATUS_LABEL_VI map để hiển thị; cập nhật
  tests/rendered-html.test.mjs và e2e theo nhãn mới.
- Xóa mọi "(Issue #…)" khỏi H1/eyebrow. Xóa link "Marketing Landing Page" khỏi sidebar.
- Navigation: 2 nhóm cho người vận hành (Tổng quan, Đơn hàng, Catalog, Nhật ký, Cài đặt) và nhóm
  "Quản trị hệ thống" chỉ hiện với role ADMIN (Luật & chính sách, ERP Outbox, Bot & kênh, Công cụ
  kiểm thử SKU, Sơ đồ quy trình, Chứng thư nhật ký).

### 6. Tiền tệ & số
- Mọi giá trị tiền qua money(value, order.currency); xóa "$…toFixed(2)". VND không thập phân,
  USD 2 thập phân (sửa money(): maximumFractionDigits theo currency).

### 7. Màn hình phụ nối API
- ERPSyncView: dữ liệu từ api.erp.getOutboxStatus; nút "Chạy đồng bộ" → processOutbox; hiển thị
  mode; trạng thái DEAD_LETTER.
- RulesView: đọc/ghi qua api.rules (GET/PUT), có nút Lưu, phản hồi lỗi.
- ExtractionReviewStudio: danh sách đơn status extraction_review từ api.orders.list({status}),
  chỉnh dòng → api.orders.confirmExtraction; hiển thị kết quả phân tích trả về.
- AuditView: GET /api/v1/audit/events mới (backend: union decisions + audit_blocks, phân trang,
  filter theo po/actor/action).
- SettingsView: KHÔNG hiển thị token; chỉ trạng thái cấu hình từ /bot/status và hướng dẫn env;
  bỏ nút Lưu giả. Thêm phần "Liên kết tài khoản Telegram" gọi /bot/telegram/link (ADMIN).
- SideBySideViewer: khi order.source_path có → hiển thị file gốc (PDF qua <iframe> tới
  GET /api/v1/orders/{id}/source (stream, VIEWER); ảnh qua <img>; JSON/CSV/TXT dạng <pre>).
  Không có → "Không có tệp gốc". Xóa "Simulated Document Source".

## Tiêu chí chấp nhận
- tsc + lint sạch. npm test (rendered-html) cập nhật nhãn tiếng Việt.
- Playwright (cập nhật apps/web/tests/e2e): login bằng key manager → upload examples/orders/po-review.json
  → thấy 2 finding thật từ API → mở modal duyệt, nhập note 5 ký tự → nút bị khóa → 12 ký tự → duyệt →
  trạng thái "Đã duyệt" lấy từ refresh (không optimistic) → xuất hiện trong Nhật ký.
- Tắt backend → UI hiện EmptyState lỗi, không hiện seed.
- grep apps/web/components không còn: "Maya", "Northwind", "Olivia", "86%", "+18%", "Issue #", "toFixed(2)".

## Bàn giao
- Commit: "feat(web): session auth, real data everywhere, Vietnamese UI, complete decision flow, wire secondary screens"
```

---

## PROMPT A8 — Landing page tách khỏi app, claim trung thực, liên hệ nhất quán

**Branch:** `fix/a8-landing-truth`

```
## Mục tiêu
Landing hiện render trong app shell (có sidebar), header bị badge đè, robots index cả app,
claim không kiểm chứng, thông tin liên hệ 3 domain/3 email khác nhau, form lead không gửi đi đâu.

## Bằng chứng
- apps/web/app/(protected)/landing/page.tsx  nằm trong route group protected
- LandingPageView.tsx:102 handleLeadSubmit chỉ setState; :1415 mailto huynh2102@gmail.com
- app/layout.tsx JSON-LD: facebook cá nhân, email cá nhân, địa chỉ nhà
- docs/PITCH_DECK_VN.md contact@popreflight.com; docs/marketing/ONE_PAGER.md pilot@po-preflight.vn, "09xx-xxx-xxx"
- LandingPageView: "99,4%", "100%", "Zero-Hallucination", "SOX 404", "<15ms", "SAP S/4HANA" logo

## Yêu cầu
1. Di chuyển landing ra apps/web/app/(marketing)/page.tsx (route "/"), layout riêng không sidebar,
   không AppStateProvider. App chuyển sang /app/* (hoặc giữ /overview,/orders… nhưng dưới (protected)
   với middleware login). robots.ts: allow "/" và "/pricing", disallow "/app", "/orders", "/overview"…
   sitemap chỉ trang marketing.
2. Sửa lỗi hiển thị: badge "Nhật Minh Tech" không đè logo (kiểm tra ở 1280px và 375px, chụp ảnh
   đính kèm PR).
3. Claim: thay mọi con số không có nguồn bằng mô tả năng lực kiểm chứng được:
   - "99,4% OCR", "100%", "Zero-Hallucination" → "Tự kiểm tra tổng tiền dòng so với tổng đơn; sai lệch
     bị chặn để người kiểm tra." 
   - "SOX 404 / SOC2" → "Nhật ký bất biến có chuỗi băm SHA-256, xuất được để đối soát."
   - "<15ms", "<30 giây" → "Kiểm tra tự động trong vài giây với file Excel/CSV/PDF có chữ."
   - "SAP S/4HANA" → hàng đầu là MISA AMIS, Bravo, Fast, Odoo, SAP Business One (ghi rõ trạng thái:
     "đang tích hợp" nếu chưa có khách chạy thật).
   - ROI: chuyển thành "ước tính cho doanh nghiệp X đơn/ngày" với công thức và giả định hiển thị,
     có nút "Tính cho doanh nghiệp bạn" (form đơn giản, tính client-side).
4. Liên hệ: một domain (chọn popreflight.vn), một email công ty (env NEXT_PUBLIC_CONTACT_EMAIL),
   một hotline (env). JSON-LD: bỏ founder facebook cá nhân, bỏ địa chỉ nhà; giữ Organization tối
   thiểu. Đồng bộ docs/PITCH_DECK_VN.md, docs/marketing/ONE_PAGER.md, README.
5. Form lead: POST /api/v1/leads (không auth, rate-limit 5/phút/IP, honeypot field) → lưu bảng
   leads (name, company, phone, email, erp, volume, note, created_at, ip_hash) + gửi email qua
   SMTP nếu cấu hình (env SMTP_*), nếu không → log + vẫn lưu DB. Trả 201, FE hiện "Đã nhận, chúng
   tôi liên hệ trong 1 ngày làm việc". Thêm GET /api/v1/leads (ADMIN).
6. Thêm trang /pricing với 3 gói khung (Pilot miễn phí 30 ngày · Gói theo số đơn · On-premise) —
   để trống số tiền bằng "Liên hệ" nếu chưa quyết, nhưng phải có cấu trúc và điều khoản pilot rõ.
7. Thêm trang /security: nơi lưu dữ liệu, mã hóa, phân quyền, nhật ký, tuân thủ Nghị định 13/2023
   về dữ liệu cá nhân, tùy chọn on-premise, quy trình xóa dữ liệu khi kết thúc hợp đồng.

## Tiêu chí chấp nhận
  a) GET / không chứa class "sidebar"; GET /orders chưa login → redirect /login.
  b) grep apps/web và docs/ không còn "SOX", "SOC2", "Zero-Hallucination", "99.4", "popreflight.com",
     "po-preflight.vn", "09xx".
  c) POST /leads hợp lệ → 201 và có row; honeypot điền → 200 giả (không lưu); 6 request/phút → 429.
  d) Lighthouse SEO ≥ 90 cho "/", robots chặn /orders.
  e) Ảnh chụp landing 1280 & 375 không có phần tử đè nhau.

## Bàn giao
- Commit: "fix(marketing): separate landing from app, truthful claims, unified contact, lead capture, pricing & security pages"
```

---

## PROMPT A9 — Cấu hình, CI, deploy nhất quán

**Branch:** `fix/a9-config-ci`

```
## Mục tiêu
Biến môi trường khai trong .env.example không được đọc; cổng deploy lệch; Python version lệch;
CI không chạy FE; deploy không đóng gói web.

## Bằng chứng
- .env.example: PREFLIGHT_DB_PATH, CATALOG_PATH — src/ không đọc (deps.py hardcode)
- scripts/deploy-remote.sh:16 curl :8000 — Makefile/Docker dùng 8001
- .venv Python 3.14; CI 3.11/3.12; Dockerfile 3.11
- .github/workflows/deploy.yml tar chỉ src tests examples scripts
- scripts/test.sh chạy npm chỉ "if command -v npm"

## Yêu cầu
1. Tạo src/preflight/config.py dùng pydantic-settings: Settings(env, auth_required, database_url,
   catalog_path, upload_dir, session_secret, cors_origins, telegram_*, zalo_*, gemini_*, erp_*,
   fx_live, rate_limit_enabled, company_name, smtp_*). Mọi os.getenv trong src/ thay bằng
   get_settings(). Validate lúc startup: production thiếu session_secret / webhook secret / api key
   → thoát với thông báo liệt kê thiếu gì. In ra bảng cấu hình (che secret) khi khởi động.
2. .env.example khớp 1-1 với Settings (tự sinh bằng script scripts/gen_env_example.py, có test
   so khớp).
3. Pin Python: pyproject requires-python ">=3.12,<3.13"; CI matrix ["3.12"]; Dockerfile 3.12;
   .python-version 3.12; README hướng dẫn.
4. Makefile PORT và deploy-remote.sh cùng đọc PORT (mặc định 8001); systemd unit mẫu
   infra/systemd/po-preflight.service dùng EnvironmentFile=/etc/po-preflight.env.
5. CI (.github/workflows/ci.yml): job backend (unittest + ruff check + mypy --strict cho
   services/, rules*.py, erp/payload.py), job frontend (npm ci, tsc, lint, npm test, playwright
   với backend chạy nền), job docker build. Thêm ruff + mypy vào [project.optional-dependencies].dev.
6. Deploy: đóng gói cả apps/web/dist (build trong CI) hoặc chuyển sang docker image push GHCR +
   compose pull trên server. Chọn docker; deploy-remote.sh chạy `docker compose pull && up -d`
   rồi kiểm tra /health/ready trên PORT.
7. Terraform: thêm RDS Postgres (db.t4g.micro), S3 bucket uploads (private, SSE), Secrets Manager
   cho env; EC2 user-data cài docker. Giữ chi phí tối thiểu; biến `enable_rds` mặc định false.
8. Xóa .cursor/, .agents/ khỏi repo nếu không dùng; giữ AGENTS.md nhưng cập nhật mục "Frontend
   Stack" (đã đổi auth/landing).

## Tiêu chí chấp nhận
  a) PREFLIGHT_ENV=production không SESSION_SECRET → startup exit code ≠0, log liệt kê biến thiếu.
  b) CATALOG_PATH trỏ file khác → /catalog trả dữ liệu file đó.
  c) CI xanh cả 3 job; playwright chạy được trong CI.
  d) `python scripts/gen_env_example.py --check` pass.
  e) docker build thành công với Python 3.12; image chạy /health/ready 200.

## Bàn giao
- Commit: "chore(config,ci): typed settings, single Python version, full-stack CI, docker-based deploy"
```

---

# GIAI ĐOẠN B — P1: ĐÚNG NGHIỆP VỤ NHÀ PHÂN PHỐI VIỆT NAM

Mục tiêu giai đoạn: một Sales Admin của NPP FMCG/dược dùng được 2 tuần không gặp "hệ thống không hiểu đơn của tôi".

---

## PROMPT B1 — Data model v2 và migration runner

**Branch:** `feat/b1-data-model-v2`

```
## Mục tiêu
Store hiện 1.342 dòng duy trì tay 2 chuỗi SCHEMA, không migration, dòng hàng chôn trong order_json,
không có khách hàng, không có revision. Chuyển sang SQLAlchemy Core + Alembic với schema quan hệ.

## Bằng chứng
- src/preflight/store.py:24-195   SQLITE_SCHEMA & POSTGRES_SCHEMA song song
- ux_analyses_po UNIQUE(po_number) toàn cục
- dashboard.py:26-45 tải 500 row parse JSON để đếm finding

## Yêu cầu
1. Thêm dependencies: sqlalchemy>=2.0, alembic>=1.13. Tạo src/preflight/db/ (engine.py, models.py
   dùng SQLAlchemy Core Table, không ORM session để giữ store rõ ràng), src/preflight/migrations/
   (alembic.ini, env.py, versions/). Engine từ Settings.database_url; SQLite bật WAL + foreign_keys.
2. Schema v2 (Alembic 0001_baseline tạo từ trống; 0002_import_legacy đọc bảng cũ nếu tồn tại):
   - organizations(id, code, name, created_at)  -- chuẩn bị multi-tenant; mọi bảng nghiệp vụ có org_id
   - users(id, org_id, username, display_name, email, password_hash NULL, role, is_active, created_at)
   - api_keys(id, user_id, key_hash, label, last_used_at, revoked_at)
   - channel_identities(id, user_id, channel, external_id, created_at) UNIQUE(channel, external_id)
   - customers(id, org_id, code, name, normalized_name, tax_code NULL, tier NULL, created_at)
     UNIQUE(org_id, code)
   - customer_aliases(id, customer_id, alias_normalized) UNIQUE(customer_id, alias_normalized)
   - products(id, org_id, sku, name, unit_price, stock, active, base_uom, moq, pack_size, category,
     barcode, updated_at) UNIQUE(org_id, sku)   -- catalog chuyển vào DB; CSV là nguồn import
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
   - audit_blocks(...) như cũ + order_id, request_id
   - erp_outbox(...) như A3 + order_id, next_attempt_at
   - rule_policies(org_id PK, policy_json, updated_by, updated_at)
   - sku_alias_learning(id, customer_id, raw_query_normalized, product_id, confidence, created_at)
   - leads(...) từ A8
   status (vòng đời) tách khỏi rule_status (kết quả luật): status ∈ {received, extraction_review,
   analyzed, approved, rejected, needs_changes, superseded, exported}; rule_status ∈
   {ready_for_approval, review_required, blocked}. Không ghi đè nhau nữa.
3. Viết lại store thành các repository nhỏ trong src/preflight/repositories/: orders.py, customers.py,
   products.py, decisions.py, audit.py, outbox.py, policies.py, users.py. Mỗi repo nhận Connection.
   BaseAuditStore giữ như facade tương thích tạm cho route cũ, đánh dấu deprecated, xóa ở cuối B.
4. Unit of work: routes dùng dependency `get_db()` yield Connection trong transaction; commit khi
   thành công, rollback khi exception. Không còn connection.commit rải rác.
5. Migration dữ liệu cũ (0002): analyses → orders+order_lines (customer tạo theo normalized_name,
   code tự sinh C0001…), findings_json → findings, decisions map actor chuỗi → users tạm
   (username = actor), audit_blocks giữ. Có script `preflight db upgrade` (CLI) và `preflight db
   check` (so schema vs metadata).
6. get_dashboard_stats dùng SQL GROUP BY trên findings/orders; không parse JSON.
7. Seed dev: `preflight seed-demo` tạo org "demo", 3 khách, catalog từ CSV, 4 đơn mẫu — thay
   seed_initial_data trong lifespan (không seed tự động ở production).

## Tiêu chí chấp nhận
  a) `alembic upgrade head` trên SQLite trống và trên Postgres (TEST_DATABASE_URL) đều thành công;
     `alembic check` không lệch.
  b) DB cũ (fixture tests/fixtures/legacy_preflight.db) → upgrade → số đơn, số quyết định, số
     audit block khớp; order_lines đúng số dòng.
  c) Toàn bộ test hiện có pass qua facade; test mới cho repositories.
  d) Khách A và khách B cùng po_number "PO-001" → 2 đơn riêng, không lỗi.
  e) dashboard/stats trả cùng số với truy vấn SQL kiểm chứng trong test.
  f) Không còn chuỗi SQLITE_SCHEMA/POSTGRES_SCHEMA trong src/.

## Bàn giao
- Commit: "feat(db): relational schema v2 with Alembic migrations, repositories, legacy import"
```

---

## PROMPT B2 — Dòng hàng v2: VAT, chiết khấu, khuyến mãi, UOM

**Branch:** `feat/b2-line-item-v2`

```
## Mục tiêu
PO Việt Nam có VAT 8/10%, chiết khấu dòng/đơn, hàng khuyến mãi giá 0, phí vận chuyển. Engine
hiện tổng = Σ qty×price, tax=0, giá 0 → PRICE_MISMATCH 100%.

## Yêu cầu
1. Domain (models.py): LineItem thêm discount_percent (Decimal, 0-100), discount_amount (Decimal),
   tax_rate (Decimal: 0, 5, 8, 10), is_promo (bool), description (str|None), uom (đã có), raw_sku.
   line_net = qty×unit_price − discount_amount − qty×unit_price×discount_percent/100;
   line_tax = line_net × tax_rate/100; line_total = line_net + line_tax.
   Order thêm header_discount_amount, shipping_fee, declared_subtotal, declared_tax, declared_total
   (từ tài liệu, có thể None); properties subtotal, tax_amount, grand_total tính từ dòng + header.
2. Parsers:
   - JSON: nhận các field mới (tùy chọn).
   - CSV: cột tùy chọn discount_percent, discount_amount, tax_rate, is_promo, uom, description.
   - Excel: mở rộng alias: "chiết khấu", "ck", "% ck", "giảm giá", "thuế", "vat", "thuế suất",
     "tiền thuế", "khuyến mãi", "km", "tặng", "hàng tặng", "phí vận chuyển", "phí ship", "tổng trước
     thuế", "tổng sau thuế", "cộng tiền hàng". Nhận diện dòng khuyến mãi: giá 0 hoặc mô tả chứa
     "KM"/"tặng"/"khuyến mãi" → is_promo=True. Đọc tổng khai báo ở các ô "Tổng cộng/Thành tiền/
     Tổng thanh toán" (ô số cuối bảng). Nhận số dạng "1.250.000", "1,250,000", "1.250.000,50", "1 250 000".
   - OCR prompt: yêu cầu trả discount, tax_rate, is_promo theo dòng; declared_* ở header.
3. SelfReflectionVerifier: so declared_total với grand_total tính; tolerance = max(1.000đ, 0,5%);
   phân biệt 3 kết quả: khớp / lệch do làm tròn thuế (<1% và đúng khi tính lại theo từng dòng làm
   tròn) / lệch thật. Kết quả gắn vào Order dưới dạng finding TOTAL_MISMATCH (warning) chứ không
   chỉ trong ExtractedOrder.
4. rules.py:
   - PRICE_MISMATCH so unit_price (trước CK, trước thuế) với giá kỳ vọng; is_promo=True → bỏ qua
     so giá, thay bằng finding PROMO_LINE (info — thêm severity "info" vào Finding, FE hiển thị xám).
   - Thêm DISCOUNT_EXCEEDS_POLICY (warning): discount_percent > policy.max_discount_percent (mặc định 15).
   - Thêm TAX_RATE_INVALID (error) khi tax_rate không thuộc {0,5,8,10}.
   - Mọi thông điệp tiền dùng currency của đơn (không hardcode VND).
5. FE types/derive/UI: LineItem thêm các field; bảng dòng hàng thêm cột CK, Thuế, Thành tiền;
   FINDING_TITLE cho code mới; severity "Info".
6. examples: thêm po-vat-discount.xlsx và .json thể hiện đầy đủ.

## Tiêu chí chấp nhận
  a) Excel có VAT 10% + CK 5% + 1 dòng tặng giá 0 → grand_total đúng đến đồng; dòng tặng ra
     PROMO_LINE không PRICE_MISMATCH; TOTAL_MISMATCH không nổ khi khớp.
  b) declared_total lệch 2 triệu → TOTAL_MISMATCH warning với số lệch.
  c) tax_rate 7 → TAX_RATE_INVALID error → blocked.
  d) Số "1.250.000,50" parse = Decimal("1250000.50").
  e) Đơn USD → message chứa "USD".

## Bàn giao
- Commit: "feat(domain): line items with discount/VAT/promo, Vietnamese Excel aliases, total verification as finding"
```

---

## PROMPT B3 — Rules v2: hợp đồng có hiệu lực, công nợ cấu hình được, registry mã finding

**Branch:** `feat/b3-rules-v2`

```
## Yêu cầu
1. Contract price: kiểm valid_from/valid_to theo ngày đơn (order_date từ tài liệu, fallback ngày
   nhận); chọn bậc min_quantity cao nhất thỏa; hết hạn → CONTRACT_PRICE_EXPIRED (warning) và so
   với giá catalog.
2. Credit: ngưỡng cấu hình trong RulePolicy: overdue_grace_days (mặc định 30), credit_limit_block_percent
   (mặc định 20), credit_hold_behaviour ("block"|"review"). ON_HOLD → CUSTOMER_ON_HOLD (warning).
   Exposure = outstanding + grand_total (sau thuế). Message theo currency đơn; nếu đơn khác tiền tệ
   với credit_limit → quy đổi qua ctx.fx_rates, nêu tỷ giá.
3. Duplicate: chuyển sang B4.
4. Stock: dùng ctx.available_stock(product) (B7 sẽ cung cấp ATP; hiện = stock − safety_margin).
5. Registry: src/preflight/findings_registry.py — một danh sách FindingSpec(code, default_severity,
   title_vi, description_vi, category ∈ {catalog, price, stock, credit, document, duplicate, fx})
   là nguồn duy nhất; rules.py chỉ tạo Finding qua registry.make(code, **fmt). Sinh
   apps/web/app/lib/findings.generated.ts bằng script scripts/gen_findings_ts.py; CI kiểm lệch.
6. Rule explainability: Finding thêm evidence: dict (expected, actual, source, rule_version).
   Ví dụ PRICE_MISMATCH: {"po_price":"17600000","expected_price":"18500000","source":"catalog",
   "tolerance_percent":"0","rule_version":"2.0"}. FE hiển thị bảng "Kỳ vọng / Thực tế / Nguồn"
   thay chuỗi hardcode "Grounding rule … Catalog v2026.08".
7. RulePolicy có version; mỗi Analysis lưu policy_version và catalog_snapshot_at để tái lập
   (PRD FR-027/FR-053).

## Tiêu chí chấp nhận
  a) hợp đồng hết hạn hôm qua → CONTRACT_PRICE_EXPIRED + PRICE_MISMATCH theo catalog.
  b) grace 45 ngày trong policy → nợ 40 ngày không ra OVERDUE_DEBT_BLOCKED; 30 → có.
  c) ON_HOLD → review_required, không blocked.
  d) gen_findings_ts --check pass; FE dùng title từ file sinh, xóa FINDING_TITLE thủ công.
  e) mọi finding qua HTTP có evidence là object có ≥2 khóa.

## Bàn giao
- Commit: "feat(rules): contract validity, configurable credit policy, findings registry with structured evidence"
```

---

## PROMPT B4 — Tái nộp PO bằng revision; trùng lặp đúng nghĩa

**Branch:** `feat/b4-revisions-duplicates`

```
## Mục tiêu
Hiện khách sửa và gửi lại cùng số PO → IntegrityError → đánh DUPLICATE_PO, blocked. Vòng
"Yêu cầu sửa → nộp lại" không thể xảy ra. Đồng thời cần phát hiện trùng thật (cùng khách, cùng
hàng, gửi 2 kênh).

## Yêu cầu
1. Upload/ingest khi (customer_id, po_number) đã tồn tại:
   - Đơn cũ ở needs_changes / rejected / extraction_review → tạo revision+1, đơn cũ → superseded,
     supersedes_order_id trỏ về; KHÔNG finding DUPLICATE_PO; thêm finding REVISED_ORDER (info) nêu
     khác biệt (dòng thêm/bớt/đổi qty/giá) qua diff chuẩn hóa.
   - Đơn cũ ở approved / exported → DUPLICATE_PO (error) như hiện tại, kèm evidence link đơn cũ.
   - Đơn cũ ở analyzed/received (chưa quyết định) → hỏi: tham số query ?on_conflict=revise|reject
     (mặc định reject → 409 DUPLICATE_PENDING với gợi ý). UI hiện dialog "Đơn này đang chờ duyệt.
     Thay bằng bản mới?".
2. Near-duplicate: sau phân tích, tìm đơn cùng customer trong 14 ngày có Jaccard(set(sku,qty)) ≥ 0,9
   và |total diff| < 1% → POSSIBLE_DUPLICATE (warning) với danh sách PO nghi trùng.
3. Trạng thái superseded không hiện trong hàng đợi mặc định; chi tiết đơn có mục "Các phiên bản"
   liệt kê revision, ai gửi, khác gì.
4. DecisionService: needs_changes lưu thêm `requested_changes` (text) và gửi thông báo (Telegram/
   Zalo nếu có identity của người tạo đơn; email nếu C1) — hiện chỉ ghi DB.
5. UI: nút "Tải bản sửa" trong đơn needs_changes mở UploadModal với po_number điền sẵn.

## Tiêu chí chấp nhận
  a) upload → needs_changes → upload lại cùng PO khác qty → revision 2, cũ superseded, có REVISED_ORDER
     nêu "LAPTOP-A14: 10 → 8".
  b) upload lại PO đã approved → DUPLICATE_PO error.
  c) đang analyzed, upload lại không tham số → 409 DUPLICATE_PENDING; với on_conflict=revise → revision 2.
  d) 2 khách khác nhau cùng "PO-001" → không liên quan.
  e) cùng khách, PO số khác, cùng 3 dòng cùng qty trong 3 ngày → POSSIBLE_DUPLICATE.

## Bàn giao
- Commit: "feat(orders): PO revisions replace hard duplicate block; near-duplicate detection"
```

---

## PROMPT B5 — Khách hàng master và alias learning theo ID

**Branch:** `feat/b5-customer-master`

```
## Yêu cầu
1. API CRUD /api/v1/customers (MANAGER): code, name, tax_code, tier, aliases[]. Import CSV
   (code,name,tax_code,tier,aliases dùng ";").
2. Resolver khách hàng khi ingest: src/preflight/services/customer_resolver.py:
   - Chuẩn hóa tên (bỏ dấu, hoa, bỏ loại hình DN, bỏ ký tự đặc biệt) → tra customers.normalized_name
     và customer_aliases; tra tax_code nếu tài liệu có MST (Excel/OCR trích "Mã số thuế"/"MST").
   - Không khớp chính xác → RapidFuzz token_set_ratio ≥ 90 → khớp kèm finding CUSTOMER_FUZZY_MATCHED
     (warning, evidence: tên gốc, khách chọn, điểm); < 90 → đơn vào extraction_review với
     CUSTOMER_UNRESOLVED (error) và UI cho chọn khách / tạo mới. Khi người dùng chọn → lưu alias.
3. SKU alias learning (customer_aliases cũ) chuyển sang sku_alias_learning theo customer_id;
   HybridSKUMatcher Tier-0 tra theo customer_id. Xóa CUSTOMER_HISTORICAL_NICKNAMES hardcode trong
   rag/llm_fallback.py; Tier-4 tra sku_alias_learning + lịch sử order_lines của khách (raw_sku →
   sku đã xác nhận) trước khi gọi LLM.
4. Contract price, credit, aliases đều khóa theo customer_id; xóa normalize_customer_key tạm từ A1.
5. UI: trang Khách hàng (Sales Admin): danh sách, chi tiết (giá hợp đồng, công nợ, alias SKU đã học,
   lịch sử đơn). Staging: dropdown chọn khách khi CUSTOMER_UNRESOLVED.

## Tiêu chí chấp nhận
  a) "CTY TNHH ABC" và "Công ty TNHH A.B.C" → cùng customer sau normalize; "ABC Trading" → fuzzy 90+.
  b) tên lạ → extraction_review + CUSTOMER_UNRESOLVED; confirm chọn khách → alias lưu; lần sau khớp Tier-0.
  c) dòng "dây mạng 3m" được người dùng sửa thành CAB-CAT6-3M cho khách X → lần sau khách X khớp
     Tier-0, khách Y không.
  d) grep src/ không còn "NORTHSTAR", "VINGROUP", "ACME".

## Bàn giao
- Commit: "feat(customers): customer master, resolver with fuzzy match, per-customer SKU alias learning"
```

---

## PROMPT B6 — Người dùng, mật khẩu, ma trận duyệt theo giá trị

**Branch:** `feat/b6-users-approval-matrix`

```
## Yêu cầu
1. Users có password_hash (argon2 qua `argon2-cffi`), POST /auth/login {username,password}; API key
   là bí danh của user (api_keys). Env PREFLIGHT_*_KEY chỉ dùng bootstrap admin lần đầu (tạo user
   admin nếu bảng trống), sau đó vô hiệu. CLI `preflight users create/reset-password/list`.
2. Roles: viewer, sales_admin (upload, sửa extraction, yêu cầu sửa), manager (duyệt đến hạn mức),
   director (duyệt mọi mức), auditor (đọc nhật ký), admin. Cập nhật RBAC.
3. Approval matrix trong RulePolicy: tiers = [{max_amount: 50_000_000, min_role: manager},
   {max_amount: null, min_role: director}]; điều kiện bổ sung: có finding CREDIT_LIMIT_EXCEEDED →
   min_role director. DecisionService kiểm: role đủ theo grand_total và findings; không đủ → 403
   APPROVAL_LEVEL_INSUFFICIENT với thông điệp "Đơn {total} cần cấp {role}". Route notification:
   hitl_dispatch gửi tới user có role phù hợp (channel_identities).
4. Separation of duties: người tạo/sửa đơn không được duyệt chính đơn đó (policy bật/tắt, mặc định bật).
5. UI: trang Quản trị người dùng (admin); modal duyệt hiển thị "Cần cấp: Trưởng phòng/Giám đốc".

## Tiêu chí chấp nhận
  a) manager duyệt đơn 80 triệu với tier 50 triệu → 403 APPROVAL_LEVEL_INSUFFICIENT; director → 200.
  b) sales_admin upload đơn rồi tự duyệt → 403 (SoD).
  c) đăng nhập sai mật khẩu 5 lần → khóa 15 phút (429).
  d) key env cũ không còn dùng được sau khi có user (trừ bootstrap).

## Bàn giao
- Commit: "feat(auth): users with passwords, role hierarchy, amount-based approval matrix, separation of duties"
```

---

## PROMPT B7 — Nguồn tồn kho từ ERP và ATP

**Branch:** `feat/b7-inventory-atp`

```
## Yêu cầu
1. Interface erp/adapters/base.py thêm `fetch_inventory(skus: list[str] | None) -> list[InventorySnapshot]`
   (sku, warehouse, on_hand, reserved, as_of). Mock adapters đọc CSV; live adapters (Odoo stock.quant,
   MISA inventory API, SAP MaterialStock) triển khai tối thiểu Odoo + MISA (MISA có thể chưa test
   thật → mode dry_run rõ).
2. Bảng inventory_snapshots(product_id, warehouse, on_hand, reserved, as_of, source). Job
   `preflight inventory sync` (CLI; C2 sẽ lịch hóa) ghi snapshot; products.stock = Σ on_hand.
3. ATP = on_hand − reserved_erp − allocated_local, trong đó allocated_local = Σ base_quantity của
   order_lines thuộc đơn status approved và chưa exported (outbox chưa SENT). Khi outbox SENT → đơn
   exported → không tính nữa (ERP đã trừ). Khi rejected/superseded → không tính.
4. RuleContext.available_stock(product) dùng ATP; INSUFFICIENT_STOCK evidence gồm on_hand, reserved,
   allocated_local, as_of. Nếu snapshot cũ hơn policy.inventory_stale_hours (mặc định 24) →
   INVENTORY_STALE (warning).
5. UI Catalog: cột "Tồn khả dụng" và thời điểm cập nhật; cảnh báo stale.

## Tiêu chí chấp nhận
  a) stock 10; đơn A approved 6 chưa export; đơn B 5 → INSUFFICIENT_STOCK (ATP 4).
  b) đơn A exported → đơn B mới không còn finding (snapshot giả lập on_hand 4).
  c) snapshot 30 giờ tuổi → INVENTORY_STALE.

## Bàn giao
- Commit: "feat(inventory): ERP inventory snapshots and available-to-promise with local allocations"
```

---

## PROMPT B8 — Observability thật

**Branch:** `feat/b8-observability`

```
## Yêu cầu
1. Logging: structlog hoặc logging.config với JSON formatter khi PREFLIGHT_LOG_FORMAT=json (mặc định
   ở production), màu khi dev. Mọi log có request_id, user_id, order_id (contextvars). Xóa ANSI
   trong production.
2. request_id lan truyền: audit_blocks.request_id, erp_outbox.request_id, decisions.request_id;
   header X-Request-ID trả về mọi response kể cả lỗi.
3. OpenTelemetry (optional deps `otel`): FastAPI instrumentation, span cho parse/rules/sku_resolve/
   erp_sync/ocr; exporter OTLP khi OTEL_EXPORTER_OTLP_ENDPOINT có, ngược lại tắt.
4. Sentry optional (SENTRY_DSN).
5. Metrics: record_order_processed và record_sku_resolution hiện không ai gọi → gọi đúng chỗ;
   thêm histogram thời gian phân tích, đếm finding theo code, độ tuổi outbox pending.
6. Admin page /admin/health trong UI: modes, DB, outbox pending/dead-letter, snapshot tồn kho tuổi,
   10 lỗi 5xx gần nhất (bảng request_errors lưu 7 ngày).
7. Runbook docs/RUNBOOK.md: cách tra request_id từ toast lỗi → log → audit; cách xử lý DEAD_LETTER;
   cách rotate secret; cách restore DB.

## Tiêu chí chấp nhận
  a) log JSON có request_id trùng header response và trùng audit_blocks.request_id cho cùng upload.
  b) /metrics có po_preflight_findings_total{code=...} sau upload.
  c) lỗi 500 giả xuất hiện trong /admin/health.

## Bàn giao
- Commit: "feat(observability): structured logs with request correlation, OTel/Sentry optional, real metrics, runbook"
```

---

# GIAI ĐOẠN C — P2: SẴN SÀNG PILOT

Mục tiêu: một NPP thật dùng 30 ngày; số liệu pilot thay claim.

---

## PROMPT C1 — Nhận PO qua email

**Branch:** `feat/c1-email-intake`

```
## Yêu cầu
1. Service src/preflight/intake/email.py: kết nối IMAP (env IMAP_HOST/USER/PASSWORD/FOLDER, hoặc
   Gmail API OAuth nếu có GOOGLE_*), poll mailbox mỗi N phút (C2 lịch hóa; CLI `preflight intake
   email --once`), lấy mail chưa đọc có đính kèm .xlsx/.xls/.csv/.pdf/.png/.jpg/.json.
2. Mỗi đính kèm → pipeline ingest như upload; source_channel="email", metadata: from, subject,
   message_id (UNIQUE để idempotent), received_at. Người gửi (email) → tra customers (thêm cột
   contact_emails) → customer_id; không khớp → CUSTOMER_UNRESOLVED.
3. Mail không đính kèm hợp lệ → gắn nhãn/di chuyển thư mục "preflight-ignored"; lỗi parse → trả
   lời email tự động (template tiếng Việt) "Chúng tôi không đọc được file … vui lòng gửi Excel theo
   mẫu đính kèm" + đính mẫu Excel chuẩn examples/templates/PO_MAU.xlsx (tạo mới).
4. Sau phân tích → thông báo kênh duyệt như upload web; trả lời email xác nhận "Đã nhận PO {po},
   mã theo dõi {id}".
5. UI: nguồn "Email" hiển thị người gửi, tiêu đề, link tải file gốc; Cài đặt: trạng thái hộp thư,
   lần poll cuối, số thư lỗi.

## Tiêu chí chấp nhận (dùng server IMAP giả lập trong test, ví dụ `aioimaplib` mock hoặc GreenMail
qua docker trong CI)
  a) 1 mail 2 đính kèm xlsx → 2 đơn; gửi lại cùng message_id → không tạo thêm.
  b) mail chỉ có .docx → di chuyển ignored + auto-reply có mẫu.
  c) người gửi có trong contact_emails → customer đúng.

## Bàn giao
- Commit: "feat(intake): IMAP/Gmail email ingestion with idempotent processing and auto-reply"
```

---

## PROMPT C2 — Hàng đợi việc nền và Redis

**Branch:** `feat/c2-job-queue`

```
## Yêu cầu
1. Thêm `arq` + Redis (env REDIS_URL). Jobs: analyze_order(order_id), run_ocr(order_id),
   outbox_dispatch(), inventory_sync(), email_poll(), notify(order_id). Worker: `preflight worker`.
   Cron: outbox 1 phút, inventory 30 phút, email 2 phút (cấu hình).
2. Upload: nếu file cần OCR (SCANNED_PDF/IMAGE) → tạo order status received, enqueue run_ocr, trả
   202 với order_id; UI hiển thị "Đang bóc tách…" và cập nhật qua SSE. File deterministic vẫn xử
   lý đồng bộ (nhanh) nhưng qua cùng hàm service để một đường code.
3. EventBus: khi REDIS_URL có → pub/sub Redis để nhiều worker uvicorn cùng phát SSE; không có →
   in-memory (dev) và /system/modes ghi "sse":"single_process".
4. Rate limiter: Redis-backed khi có Redis.
5. Graceful shutdown; job retry với backoff; dead-letter job ghi request_errors.

## Tiêu chí chấp nhận
  a) upload PNG → 202, sau worker chạy → status analyzed, SSE nhận "order.analyzed".
  b) 2 process uvicorn + Redis: SSE từ process A nhận sự kiện tạo ở process B (test tích hợp docker).
  c) worker chết giữa outbox_dispatch → event về PENDING sau lease timeout, không mất, không gửi trùng.

## Bàn giao
- Commit: "feat(infra): arq job queue, Redis-backed SSE and rate limiting, async OCR"
```

---

## PROMPT C3 — Connector MISA AMIS thật (hoặc ERP pilot chọn)

**Branch:** `feat/c3-misa-live`

```
## Điều kiện trước: có tài khoản sandbox MISA AMIS (hoặc ERP pilot: Bravo/Fast/Odoo).
Nếu chưa có → DỪNG, không viết code "đoán" API. Ghi vào docs/erp/MISA.md những gì cần từ khách.

## Yêu cầu (khi có sandbox)
1. Đọc tài liệu API chính thức; ghi lại endpoint auth, tạo đơn bán, tra tồn, tra khách, mã lỗi vào
   docs/erp/MISA.md. Sửa misa_live.py theo tài liệu thật (URL hiện "https://api.misa.vn/amis/v1" là
   đoán).
2. Mapping: customer → account_object (tra theo tax_code/code, tạo nếu policy cho phép), sku →
   inventory_item_code, uom, tax_rate, discount; header: PO number vào trường tham chiếu; ghi chú
   "PO Preflight #{order_id}".
3. Contract tests với sandbox (chạy khi MISA_SANDBOX_TOKEN có): tạo đơn 3 dòng → đọc lại → so khớp
   từng trường; gửi trùng idempotency → không tạo 2.
4. Reconciliation job: mỗi giờ so outbox SENT với ERP (tồn tại? tổng khớp?) → lệch → finding hệ
   thống RECONCILIATION_MISMATCH vào /admin/health và thông báo admin.
5. UI ERP Outbox: link mở chứng từ trong ERP, nút "Đối soát ngay".

## Bàn giao
- Commit: "feat(erp): MISA AMIS live connector verified against sandbox, reconciliation job"
```

---

## PROMPT C4 — Zalo OA và Telegram cho quản lý thật

**Branch:** `feat/c4-channels-live`

```
## Yêu cầu
1. Zalo OA: đọc tài liệu OA v3 chính thức; hiện payload dùng template "media" với nút oa.query.show —
   xác minh loại tin nhắn được phép gửi cho user chưa follow/ngoài 48h (ZNS cần template duyệt).
   Triển khai: (a) tin tương tác OA cho user đã follow, (b) ZNS template "PO cần duyệt" (đăng ký
   template, lưu template_id vào Settings). Refresh token tự động (đã có hàm) + lưu token vào DB
   (bảng channel_tokens, mã hóa bằng SESSION_SECRET).
2. Webhook Zalo: xác minh chữ ký theo tài liệu (hiện công thức sha256(app_id+body+timestamp+secret)
   là đoán — kiểm tra lại), chống replay (timestamp ±5 phút, lưu event_id đã xử lý).
3. Telegram: xử lý callback trả answerCallbackQuery (hiện không gọi → nút xoay mãi); cập nhật
   message sau quyết định ("✅ Đã duyệt bởi Nguyễn A lúc 10:32"); lệnh /link <mã> để tự liên kết
   tài khoản (mã sinh trong UI Cài đặt của user).
4. Thẻ thông báo: hiển thị grand_total sau thuế, số finding theo severity, 3 finding đầu tiếng Việt,
   link deep-link vào đơn (yêu cầu login).
5. Escalation: đơn chờ > policy.escalation_hours (mặc định 4) → nhắc lại; > 24h → gửi cấp trên.

## Tiêu chí chấp nhận
  a) Telegram: bấm duyệt → answerCallbackQuery được gọi (mock HTTP), message được edit.
  b) Zalo webhook replay cùng event_id → bỏ qua.
  c) /link mã đúng → channel_identities có bản ghi; mã hết hạn 10 phút → lỗi.
  d) Test tay với 1 tài khoản Zalo/Telegram thật, ghi lại ảnh chụp trong PR.

## Bàn giao
- Commit: "feat(channels): production Zalo OA/ZNS flow, Telegram callback UX, self-service account linking, escalation"
```

---

## PROMPT C5 — Embedding thật cho Tier-3 và bộ eval theo khách

**Branch:** `feat/c5-real-embeddings`

```
## Yêu cầu
1. Thay VectorSemanticMatcher (bag-of-words + synonym map tay) bằng embedding đa ngữ chạy cục bộ:
   `fastembed` với model BAAI/bge-m3 (hoặc intfloat/multilingual-e5-small nếu cần nhẹ). Index
   trong SQLite (bảng product_embeddings, vector blob) với brute-force cosine (catalog < 50k SKU đủ
   nhanh) — chưa cần ChromaDB. Cập nhật docs: xóa "ChromaDB", "TF-IDF trigram".
2. Văn bản nhúng = sku + name + category + aliases đã học + mô tả. Rebuild khi catalog đổi (job).
3. Ngưỡng: tự tính từ eval (mục 5), không hardcode 0.35/0.70.
4. Tier-4 LLM: dùng Gemini qua SDK chính thức (google-genai) với structured output; timeout, retry,
   circuit breaker; log token usage; chỉ gọi khi Tier 0–3 < ngưỡng; luôn ràng buộc trả về SKU trong
   danh sách ứng viên top-20 (không toàn catalog — hiện gửi cả catalog mỗi lần).
5. Eval: mở rộng evals/ground_truth.json → evals/<customer>/aliases.jsonl (raw, expected_sku) thu
   từ dữ liệu thật của pilot (ẩn danh). scripts/run_evals.py in precision@1, recall, tỉ lệ rơi
   xuống Tier-4, chi phí; lưu evals/results/<date>.json; CI fail nếu precision@1 giảm >2 điểm so
   baseline.
6. UI "Công cụ kiểm thử SKU" (admin) hiển thị 3 ứng viên với điểm và tier; nút "Đúng là mã này" →
   ghi alias learning.

## Tiêu chí chấp nhận
  a) "dây mạng 3m bấm sẵn" → CAB-CAT6-3M top-1 với embedding, không cần synonym map.
  b) run_evals trên bộ hiện có ≥ baseline; báo cáo có tỉ lệ Tier-4.
  c) Gemini lỗi → circuit OPEN sau 3 lần, resolve trả unresolved ngay với lý do "LLM tạm ngưng".

## Bàn giao
- Commit: "feat(rag): local multilingual embeddings for tier-3, constrained LLM tier-4, evaluation harness"
```

---

## PROMPT C6 — Frontend sẵn sàng pilot

**Branch:** `feat/c6-frontend-pilot`

```
## Yêu cầu
1. Màn Đơn hàng: chỉnh sửa dòng hàng ngay trong chi tiết (inline) cho đơn extraction_review /
   needs_changes: đổi SKU (dropdown tìm kiếm gọi /sku/resolve), qty, giá, UOM; "Lưu & chạy lại
   kiểm tra" → confirm-extraction. Không còn Staging Studio tách rời — gộp vào chi tiết đơn.
2. Xem tài liệu gốc: PDF.js (cdnjs) render trang, ảnh zoom; với OCR có bounding box (nếu Gemini trả
   về) → highlight dòng khi hover.
3. Bảng hàng đợi: sắp xếp, lọc theo khách/trạng thái/ngày/severity, phân trang server-side
   (list API có total), lưu bộ lọc vào URL.
4. Trạng thái rỗng, đang tải, lỗi cho mọi màn; toast lỗi có "Mã tham chiếu" (request_id) và nút
   sao chép.
5. Accessibility: focus trap + Escape cho modal, aria-live cho toast, kiểm tra contrast WCAG AA cả
   2 theme (script kiểm tra tự động trong test).
6. Mobile: màn duyệt tối giản /m/orders/{id} cho quản lý mở từ Telegram/Zalo: tổng, finding, 3 nút.
7. Xóa khỏi nav khách hàng: LangGraph Visualizer, RAG Tester, Merkle Certificate → /admin/tools.
   Đổi tên "Merkle Certificate" → "Chứng thư nhật ký (chuỗi băm SHA-256)".
8. Playwright: 6 hành trình: login; upload Excel VAT/CK → sửa SKU inline → duyệt (manager) → bị chặn
   theo hạn mức → director duyệt → xem outbox; tái nộp PO needs_changes; mobile approve.

## Tiêu chí chấp nhận
- Playwright 6/6 xanh trong CI; axe-core không lỗi serious/critical; tsc/lint sạch.

## Bàn giao
- Commit: "feat(web): inline extraction correction, source viewer, server-side queue, mobile approval, a11y"
```

---

## PROMPT C7 — Đo lường pilot

**Branch:** `feat/c7-pilot-metrics`

```
## Yêu cầu
1. Sự kiện đo (bảng metrics_events hoặc từ dữ liệu có sẵn): thời gian từ nhận → analyzed; từ
   analyzed → quyết định; số dòng người sửa / tổng dòng; số finding theo code; số đơn chặn trước ERP;
   số DUPLICATE/POSSIBLE_DUPLICATE; chi phí LLM/OCR theo đơn; tỉ lệ Tier RAG.
2. GET /api/v1/reports/pilot?from&to (MANAGER) trả JSON; /reports/pilot.csv; trang "Báo cáo" trong UI
   với biểu đồ đơn giản (SVG tự vẽ, không thư viện nặng).
3. Email tuần tự động cho admin (template tiếng Việt) khi SMTP có.
4. docs/PILOT_PLAYBOOK.md: mục tiêu pilot theo PRD §18, cách đọc báo cáo, checklist 30 ngày,
   mẫu phỏng vấn Sales Admin sau tuần 1/2/4.

## Bàn giao
- Commit: "feat(reports): pilot KPI report, CSV export, weekly email, pilot playbook"
```

---

## PROMPT C8 — Tài liệu và marketing dựa trên bằng chứng

**Branch:** `docs/c8-truthful-marketing`

```
## Yêu cầu
1. README, docs/MO_TA_DU_AN.md, docs/architecture.md: cập nhật đúng hiện trạng (bảng "Thành phần |
   Trạng thái: chạy thật / dry-run / kế hoạch"). Xóa "MIT Outer System / Stanford Inner Loop",
   "Merkle", "ChromaDB", "WeChat" khỏi mô tả hiện trạng (có thể giữ ở mục "Tầm nhìn" nếu muốn).
2. Pitch deck & one-pager: thay bảng ROI giả bằng "Kết quả pilot {khách}: … " khi có; trước đó dùng
   "Cách chúng tôi đo" thay số. Bỏ SOX/SOC2; thêm Nghị định 13, on-prem, quy trình dữ liệu.
   ICP và ERP: MISA/Bravo/Fast/Odoo/SAP B1.
3. Bảng giá: hoàn thiện /pricing với số cụ thể sau khi có 2 cuộc phỏng vấn giá (ghi giả định).
4. Video demo: quay lại trên dữ liệu thật của luồng A7/C6 (không phải mock); script trong
   docs/marketing/VIDEO_DEMO_60S_SCRIPT.md cập nhật.
5. Case study template docs/marketing/CASE_STUDY_TEMPLATE.md: bối cảnh, trước/sau, số liệu từ C7,
   trích dẫn khách.
6. Tài liệu bán hàng kỹ thuật docs/SECURITY_QA.md: 20 câu kế toán trưởng/IT hay hỏi và trả lời thật.

## Bàn giao
- Commit: "docs: align all product and marketing documents with verified capabilities"
```

---

# GIAI ĐOẠN D — CHECKLIST "ĐỦ CHÍN ĐỂ ĐI CHÀO HÀNG"

Dán checklist này vào cuối; agent chạy `scripts/release_check.sh` (tạo trong A9) in ra bảng PASS/FAIL.

| # | Tiêu chí | Cách kiểm | Prompt |
|---|---|---|---|
| 1 | Không còn fallback im lặng; `/system/modes` phản ánh đúng | grep + test | A5 |
| 2 | Mọi quyết định qua DecisionService, actor từ auth | grep + test | A2 |
| 3 | Luật B2B chạy qua HTTP với master data thật | test_rule_context_http | A1 |
| 4 | ERP payload đầy đủ, idempotent, dead-letter | test_erp_payload_http | A3 |
| 5 | Lỗi API theo RFC7807, không lộ nội bộ | test_error_taxonomy | A4 |
| 6 | FE không có dữ liệu giả; login thật; 1 ngôn ngữ | grep + Playwright | A7 |
| 7 | Landing tách app; claim có nguồn; liên hệ nhất quán | grep docs+web | A8 |
| 8 | Postgres chạy thật trong docker compose | CI job | A5/A9 |
| 9 | Schema qua Alembic; `alembic check` sạch | CI | B1 |
| 10 | VAT/CK/KM/UOM parse đúng trên 20 file PO thật (ẩn danh) từ khách | evals/documents | B2 |
| 11 | Khách B dùng PO-001 không bị chặn; tái nộp tạo revision | test | B4 |
| 12 | Khách hàng master + alias theo ID | test | B5 |
| 13 | Ma trận duyệt theo giá trị, SoD | test | B6 |
| 14 | ATP và snapshot tồn từ ERP | test | B7 |
| 15 | Log JSON có request_id nối tới audit | test | B8 |
| 16 | Email intake idempotent | test | C1 |
| 17 | OCR/outbox chạy nền, SSE đa process | test docker | C2 |
| 18 | 1 connector ERP xác nhận trên sandbox thật | contract test | C3 |
| 19 | Zalo/Telegram duyệt thật từ điện thoại quản lý | ảnh chụp PR | C4 |
| 20 | precision@1 SKU ≥ 95% trên bộ eval khách pilot | run_evals | C5 |
| 21 | Playwright 6 hành trình + axe sạch | CI | C6 |
| 22 | Báo cáo pilot xuất được | test | C7 |
| 23 | Tài liệu & deck khớp năng lực | review tay | C8 |
| 24 | Backup/restore DB đã diễn tập, ghi RUNBOOK | diễn tập | B8/A9 |
| 25 | Có ít nhất 1 NPP dùng 30 ngày và đồng ý làm case study | thực tế | — |

---

## PHỤ LỤC A — MẪU BÁO CÁO CUỐI SESSION (agent phải điền)

```
## Đã làm
- [file:line] mô tả ngắn

## Kiểm chứng
- unittest: N tests, 0 fail (thời gian)
- tsc/lint: sạch
- Test mới: tên file, số test, đi qua HTTP: có/không
- Kiểm tay: bước 1…, kết quả

## Chưa làm / phát hiện ngoài phạm vi
- … (ghi rõ để tạo prompt tiếp theo)

## Rủi ro
- …
```

## PHỤ LỤC B — QUY ƯỚC ĐẶT TÊN FINDING CODE

- Danh từ_TÍNH TRẠNG, viết hoa, gạch dưới: `PRICE_MISMATCH`, `CONTRACT_PRICE_EXPIRED`, `CUSTOMER_UNRESOLVED`.
- Severity mặc định trong registry; luật có thể hạ (không nâng) theo policy.
- Mỗi code có title_vi ≤ 6 từ và description_vi 1 câu giải thích hậu quả và việc cần làm.

## PHỤ LỤC C — DANH SÁCH FINDING CODE SAU GIAI ĐOẠN B

| Code | Severity | Nhóm |
|---|---|---|
| DUPLICATE_PO | error | duplicate |
| DUPLICATE_PENDING (HTTP 409, không phải finding) | — | duplicate |
| POSSIBLE_DUPLICATE | warning | duplicate |
| REVISED_ORDER | info | document |
| UNKNOWN_SKU | error / warning (có gợi ý) | catalog |
| INACTIVE_SKU | error (→ warning nếu policy) | catalog |
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
