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
