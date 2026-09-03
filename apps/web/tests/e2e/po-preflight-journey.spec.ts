import { test, expect } from "@playwright/test";

test.describe("PO Preflight — End-to-End Enterprise Pilot Test Suite", () => {
  test("Journey 1: Login & Session Authentication flow", async ({ page }) => {
    await page.goto("/login");

    // Verify Login Gateway elements
    await expect(page.locator("text=Đăng nhập, text=Login").first()).toBeVisible();

    // Check username/password inputs
    const usernameInput = page.locator("input[type='text'], input[name='username']").first();
    const passwordInput = page.locator("input[type='password'], input[name='password']").first();

    if (await usernameInput.isVisible() && await passwordInput.isVisible()) {
      await usernameInput.fill("admin");
      await passwordInput.fill("admin123");
      const submitBtn = page.locator("button[type='submit']").first();
      await submitBtn.click();
    }

    // Verify overview or landing accessibility
    await page.goto("/overview");
    await expect(page.locator("text=Tổng quan, text=Overview").first()).toBeVisible();
  });

  test("Journey 2: Orders Queue Sorting, Filtering & URL Synchronization", async ({ page }) => {
    await page.goto("/orders");

    // Verify PO Queue header
    await expect(page.locator("h1:has-text('Đơn đặt hàng'), h1:has-text('Purchase')").first()).toBeVisible();

    // Search query test
    const searchInput = page.locator("input[placeholder*='Tìm mã PO']").first();
    await searchInput.fill("PO-10428");

    // Verify sample order is listed
    const poRow = page.locator("text=PO-10428").first();
    await expect(poRow).toBeVisible();

    // Select customer Northstar Retail
    await expect(page.locator("text=Northstar Retail").first()).toBeVisible();

    // Verify URL contains search query
    await page.waitForTimeout(300);
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
    await expect(page.locator("text=Kiểm thử SKU").first()).toBeVisible();
    await expect(page.locator("text=Chứng thư nhật ký (chuỗi băm SHA-256)").first()).toBeVisible();

    // Navigate to audit certificate
    await page.goto("/audit-certificate");
    await expect(page.locator("text=Chứng thư, text=Certificate").first()).toBeVisible();
  });

  test("Journey 6: ERP Sync Outbox & Multi-Channel Telegram/Zalo Settings", async ({ page }) => {
    // Check ERP Outbox view
    await page.goto("/erp-sync");
    await expect(page.locator("text=Đồng bộ ERP, text=ERP Sync").first()).toBeVisible();
    await expect(page.locator("text=Outbox").first()).toBeVisible();

    // Check Settings multi-channel view
    await page.goto("/settings");
    await expect(page.locator("text=Telegram Bot").first()).toBeVisible();
    await expect(page.locator("text=Zalo Official Account").first()).toBeVisible();
    await expect(page.locator("text=Webhook, text=API Token").first()).toBeVisible();
  });
});
