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

test("renders the Overview as the index page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /PO Preflight — Purchase Order Operations/);
  assert.match(html, /Operations overview/);
  assert.match(html, /Attention queue/);
  assert.match(html, /Weekly flow/);
  assert.doesNotMatch(html, /codex-preview|Starter Project|Your site is taking shape/);
});

test("renders the Orders view at /orders", async () => {
  const response = await render("/orders");
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /Purchase orders/);
  assert.match(html, /PO-10428/);
  assert.match(html, /Northstar Retail/);
  assert.match(html, /Review required/);
  assert.match(html, /Upload purchase order/);
  assert.match(html, /Request changes/);
  assert.match(html, /Review and approve/);
  assert.match(html, /Validation findings/);
  assert.match(html, /Activity/);
});

test("renders the Audit log view with working filters at /audit-log", async () => {
  const response = await render("/audit-log");
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /Audit log/);
  assert.match(html, /Search order, person, or event/);
  assert.match(html, /All events/);
  assert.match(html, /Human decisions/);
  assert.match(html, /System events/);
  assert.match(html, /Validation completed/);
  assert.match(html, /Order submitted/);
  assert.match(html, /Order blocked/);
  assert.match(html, /Order approved/);
});

test("renders the Product catalog view with working filters at /catalog", async () => {
  const response = await render("/catalog");
  assert.equal(response.status, 200);
  const html = await response.text();

  assert.match(html, /Product catalog/);
  assert.match(html, /Search SKU or product/);
  assert.match(html, /All statuses/);
  assert.match(html, /Active/);
  assert.match(html, /Inactive/);
  assert.match(html, /Catalog price/);
  assert.match(html, /Morrow task chair/);
  assert.match(html, /CHR-110/);
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
  assert.match(html, /LangGraph Stateful Workflow Visualizer/);
  assert.match(html, /Document Ingestion/);
  assert.match(html, /4-Tier Hybrid RAG/);
});

test("renders the 4-Tier RAG Playground view at /rag-playground", async () => {
  const response = await render("/rag-playground");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /4-Tier Hybrid SKU Resolution Playground/);
  assert.match(html, /Interactive SKU Query Tester/);
});

test("renders the ERP Sync Outbox view at /erp-sync", async () => {
  const response = await render("/erp-sync");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /ERP Synchronization/);
  assert.match(html, /Transactional Outbox Messages/);
});

test("renders the Cryptographic Audit Certificate view at /audit-certificate", async () => {
  const response = await render("/audit-certificate");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Cryptographic Audit Certificate Center/);
  assert.match(html, /MERKLE ROOT HASH/);
});

test("renders the Settings view at /settings", async () => {
  const response = await render("/settings");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Multi-Channel Integration/);
  assert.match(html, /Telegram Bot/);
});
