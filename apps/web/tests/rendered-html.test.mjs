import assert from "node:assert/strict";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("renders the OrderFlow operations prototype", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /OrderFlow AI — Purchase Order Operations/);
  assert.match(html, /Purchase orders/);
  assert.match(html, /PO-10428/);
  assert.match(html, /Northstar Retail/);
  assert.match(html, /Review required/);
  assert.doesNotMatch(html, /codex-preview|Starter Project|Your site is taking shape/);
});

test("renders the controlled review actions", async () => {
  const response = await render();
  const html = await response.text();
  assert.match(html, /Upload purchase order/);
  assert.match(html, /Request changes/);
  assert.match(html, /Review and approve/);
  assert.match(html, /Validation findings/);
  assert.match(html, /Activity/);
});
