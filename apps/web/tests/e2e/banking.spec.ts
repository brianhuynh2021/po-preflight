import { test, expect } from "@playwright/test";

test("banking intake, evidence, export, invalidation and API failure", async ({ page }) => {
  // Isolate frontend interactions; Python HTTP tests verify real engine/auth behavior.
  await page.route("http://localhost:8001/**", (route) => route.fulfill({ status: 503, json: { detail: "Test service unavailable" } }));
  let fail = false;
  await page.route("**/api/v1/banking/analyze", async (route) => {
    const payload = route.request().postDataJSON();
    expect(payload.requested_amount).toBe("850000000");
    expect(payload.invoices[0].source_reference).toContain("trang 1");
    if (fail) return route.fulfill({ status: 503, json: { detail: "Không kết nối được dịch vụ tiền kiểm" } });
    return route.fulfill({ json: {
      case_id: payload.case_id, status: "Blocked", mode: "pilot_manual_input", policy_version: "BANK-PILOT-1",
      evaluated_on: payload.limit_as_of, available_limit: "800000000", eligible_invoice_amount: "800000000",
      findings: [{ code: "LIMIT_EXCEEDED", severity: "error", fields: ["requested_amount"], evidence: { requested: "850000000", available: "800000000" } }],
    } });
  });
  await page.goto("/banking");
  await page.getByRole("button", { name: "Nạp hồ sơ mẫu" }).click();
  await expect(page.getByLabel("Số tiền đề nghị (VND)")).toHaveValue("850000000");
  await page.getByRole("button", { name: "Kiểm tra hồ sơ", exact: true }).click();
  const result = page.getByRole("complementary", { name: "Kết quả tiền kiểm" });
  await expect(result.getByText("Số tiền đề nghị vượt hạn mức còn lại")).toBeVisible();
  await result.getByText("Xem căn cứ đối chiếu").click();
  await expect(result.getByText("Mã kiểm tra: LIMIT_EXCEEDED")).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Tải hồ sơ và kết quả" }).click();
  expect((await download).suggestedFilename()).toBe("banking-preflight.json");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: "/tmp/banking-desktop.png", fullPage: true });
  await page.getByLabel("Khách hàng vay", { exact: true }).fill("Khách hàng đã sửa");
  await expect(result.getByText("Số tiền đề nghị vượt hạn mức còn lại")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Tải hồ sơ và kết quả" })).toHaveCount(0);
  fail = true;
  await page.getByRole("button", { name: "Kiểm tra hồ sơ", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveText("Không kết nối được dịch vụ tiền kiểm");
  await expect(result.getByText("Blocked", { exact: true })).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("heading", { name: "Tiền kiểm hồ sơ giải ngân" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: "/tmp/banking-mobile.png", fullPage: true });
});
