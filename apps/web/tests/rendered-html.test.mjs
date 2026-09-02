import assert from "node:assert/strict";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(`http://localhost${path}`, { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("renders the Marketing Landing Page as the index page without sidebar", async () => {
  const response = await render("/");
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /PO Preflight/);
  assert.match(html, /Cổng Kiểm Soát An Toàn Tự Động Cho Đơn Đặt Hàng B2B/);
  assert.match(html, /Đăng Ký Trải Nghiệm Pilot 30 Ngày/);
  assert.doesNotMatch(html, /class="sidebar"/);
});

test("renders the Operations Overview at /overview", async () => {
  const response = await render("/overview");
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /TỔNG QUAN VẬN HÀNH/);
  assert.match(html, /Operations overview/);
  assert.match(html, /Attention queue/);
  assert.match(html, /Weekly flow/);
});

test("renders the Pricing page at /pricing", async () => {
  const response = await render("/pricing");
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /BẢNG GIÁ &amp; GÓI DỊCH VỤ LINH HOẠT/);
  assert.match(html, /Gói Pilot Trải Nghiệm/);
  assert.match(html, /30 ngày miễn phí/);
  assert.match(html, /Gói Theo Số Lượng Đơn/);
  assert.match(html, /Gói Doanh Nghiệp On-Premise/);
});

test("renders the Security & Compliance page at /security", async () => {
  const response = await render("/security");
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /AN NINH DỮ LIỆU &amp; TUÂN THỦ PHÁP LÝ/);
  assert.match(html, /Nghị định 13\/2023\/NĐ-CP/);
  assert.match(html, /AES-256/);
  assert.match(html, /Nhật Ký Bất Biến SHA-256/);
});

test("renders the Orders view at /orders", async () => {
  const response = await render("/orders");
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /Đơn đặt hàng/);
  assert.match(html, /PO-10428/);
  assert.match(html, /Northstar Retail/);
  assert.match(html, /Review required/);
  assert.match(html, /Tải lên đơn hàng/);
  assert.match(html, /Từ chối/);
  assert.match(html, /Validation findings/);
});

test("renders the Audit log view with working filters at /audit-log", async () => {
  const response = await render("/audit-log");
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /Nhật ký kiểm toán/);
  assert.match(html, /Search order, person, or event/);
  assert.match(html, /All events/);
  assert.match(html, /Human decisions/);
  assert.match(html, /System events/);
});

test("renders the Product catalog view with working filters at /catalog", async () => {
  const response = await render("/catalog");
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /Product catalog/);
  assert.match(html, /Search SKU or product/);
  assert.match(html, /All statuses/);
  assert.match(html, /Active/);
  assert.match(html, /Catalog price/);
});

test("renders the Staging Studio view at /staging", async () => {
  const response = await render("/staging");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Extraction Review/);
  assert.match(html, /Extracted Line Items/);
});

test("renders the LangGraph Visualizer view at /agent-graph", async () => {
  const response = await render("/agent-graph");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Sơ đồ Luồng Tác vụ Stateful LangGraph/);
  assert.match(html, /Bóc tách tài liệu/);
  assert.match(html, /Khớp mã 4 tầng/);
});

test("renders the 4-Tier RAG Playground view at /rag-playground", async () => {
  const response = await render("/rag-playground");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Môi trường Kiểm thử Khớp mã SKU 4 Tầng/);
  assert.match(html, /Kiểm thử truy vấn SKU tương tác/);
});

test("renders the ERP Sync Outbox view at /erp-sync", async () => {
  const response = await render("/erp-sync");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Đồng bộ ERP/);
  assert.match(html, /Outbox Center/);
});

test("renders the Cryptographic Audit Certificate view at /audit-certificate", async () => {
  const response = await render("/audit-certificate");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Trung tâm Chứng thư Kiểm toán Mật mã/);
  assert.match(html, /MERKLE ROOT/);
});

test("renders the Settings view at /settings", async () => {
  const response = await render("/settings");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Cấu hình Tích hợp Đa kênh/);
  assert.match(html, /Telegram Bot/);
  assert.match(html, /Zalo Official Account/);
});

test("renders the Users & Approval Matrix view at /users", async () => {
  const response = await render("/users");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Quản lý Người dùng &amp; Ma trận Phê duyệt/);
  assert.match(html, /Tổng người dùng/);
});
