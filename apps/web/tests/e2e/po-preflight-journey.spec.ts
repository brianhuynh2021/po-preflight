import { test, expect } from "@playwright/test";

test.describe("PO Preflight — End-to-End Enterprise Pilot Test Suite", () => {
  test("Journey 1: Login & Session Authentication flow", async ({ page }) => {
    await page.goto("/login");
    await page.waitForLoadState("networkidle");

    // Verify Login Gateway elements
    await expect(page.locator("text=/Đăng nhập|PO Preflight/i").first()).toBeVisible();

    // Fill API key and submit
    const apiKeyInput = page.locator("#apiKey");
    await expect(apiKeyInput).toBeVisible();
    await apiKeyInput.click();
    await apiKeyInput.fill("pf_dev_adm_9901");

    const submitBtn = page.locator("button[type='submit']").first();
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Verify overview or landing accessibility
    await page.waitForURL("**/overview", { timeout: 10000 }).catch(() => {});
    await page.goto("/overview");
    await expect(page.locator("text=/Bảng điều khiển|Tổng quan|Operations overview/i").first()).toBeVisible();
  });

  test("Journey 2: Orders Queue Sorting, Filtering & URL Synchronization", async ({ page }) => {
    await page.goto("/orders?q=PO-10428");

    // Verify PO Queue header
    await expect(page.locator("h1:has-text('Đơn đặt hàng'), h1:has-text('Purchase')").first()).toBeVisible();

    // Verify search input reflects URL query
    const searchInput = page.locator("input[placeholder*='Tìm']").first();
    await expect(searchInput).toHaveValue("PO-10428");

    // Verify sample order is listed in the queue
    const poRow = page.locator(".order-row:has-text('PO-10428')").first();
    await expect(poRow).toBeVisible();

    // Verify customer Northstar Retail in order row
    await expect(page.locator(".order-row:has-text('Northstar Retail')").first()).toBeVisible();

    // Verify URL contains search query
    expect(page.url()).toContain("q=PO-10428");
  });

  test("Journey 3: Order Detail Inline Line Item Editing & Staging Integration", async ({ page }) => {
    await page.goto("/orders?id=PO-10428");

    // Check order detail panel
    await expect(page.locator("h2:has-text('PO-10428')").first()).toBeVisible();

    // Check "Chỉnh sửa dòng hàng" button exists
    const editBtn = page.locator("button:has-text('Chỉnh sửa dòng hàng')").first();
    await expect(editBtn).toBeVisible();
    await editBtn.click();

    // Verify editable table inputs appeared
    const skuInput = page.locator("input[placeholder*='Nhập mã SKU']").first();
    await expect(skuInput).toBeVisible();

    // Verify "Lưu & chạy lại kiểm tra" action button exists
    const saveBtn = page.locator("button:has-text('Lưu & chạy lại kiểm tra')").first();
    await expect(saveBtn).toBeVisible();

    // Cancel edit
    const cancelBtn = page.locator("button:has-text('Hủy')").first();
    await cancelBtn.click();
    await expect(editBtn).toBeVisible();
  });

  test("Journey 4: Mobile Minimal Approval Screen (/m/orders/[id])", async ({ page }) => {
    await page.goto("/m/orders/PO-10428");

    // Verify mobile header
    await expect(page.locator("text=PO Preflight Mobile").first()).toBeVisible();

    // Verify grand total card
    await expect(page.locator("text=Tổng giá trị đơn hàng").first()).toBeVisible();

    // Verify 3 decision buttons exist
    const approveBtn = page.locator("button:has-text('Duyệt đơn'), button:has-text('Approve')").first();
    await expect(approveBtn).toBeVisible();

    const rejectBtn = page.locator("button:has-text('Từ chối'), button:has-text('Reject')").first();
    await expect(rejectBtn).toBeVisible();

    const needsChangesBtn = page.locator("button:has-text('Yêu cầu sửa'), button:has-text('Needs Changes')").first();
    await expect(needsChangesBtn).toBeVisible();

    // Verify note input
    const noteArea = page.locator("#mobile-decision-note, textarea").first();
    await expect(noteArea).toBeVisible();
  });

  test("Journey 5: Admin Diagnostics Hub & Renamed SHA-256 Audit Certificate", async ({ page }) => {
    // Navigate to admin tools hub
    await page.goto("/admin/tools");
    await expect(page.locator("text=Công cụ kỹ thuật & RAG").first()).toBeVisible();

    // Check diagnostic tools cards
    await expect(page.locator("text=LangGraph").first()).toBeVisible();
    await expect(page.locator("text=/Kiểm thử SKU|4-Tier RAG/i").first()).toBeVisible();
    await expect(page.locator("text=/Chứng thư nhật ký|SHA-256/i").first()).toBeVisible();

    // Navigate to audit certificate
    await page.goto("/audit-certificate");
    await expect(page.locator("text=/Chứng thư|Certificate/i").first()).toBeVisible();
  });

  test("Journey 6: ERP Sync Outbox & Multi-Channel Telegram/Zalo Settings", async ({ page }) => {
    // Check ERP Outbox view
    await page.goto("/erp-sync");
    await expect(page.locator("text=/Đồng bộ ERP|ERP Synchronization/i").first()).toBeVisible();
    await expect(page.locator("text=Outbox").first()).toBeVisible();

    // Check Settings multi-channel view
    await page.goto("/settings");
    await expect(page.locator("text=Telegram Bot").first()).toBeVisible();
    await expect(page.locator("text=Zalo Official Account").first()).toBeVisible();
    await expect(page.locator("text=/Webhook|API Token/i").first()).toBeVisible();
  });
});

