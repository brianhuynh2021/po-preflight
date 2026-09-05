import { test } from "@playwright/test";

test("Capture Google Design System UI Audit Screenshots", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });

  // 0. Landing Page in Light Mode
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("theme", "light");
    document.dispatchEvent(new Event("preflight:themechange"));
  });
  await page.waitForTimeout(300);

  // 0a. Hero Section
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/landing_hero.png",
  });

  // 0b. Click "Xem Video Demo 60 Giây" button
  await page.click("a[href='#demo-video']");
  await page.waitForTimeout(600);

  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/landing_video_switcher_fixed.png",
  });

  // 0b2. Scroll to SKU Sandbox & ROI Calculator
  const sandbox = page.locator("#sandbox");
  if (await sandbox.isVisible()) {
    await sandbox.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    await page.screenshot({
      path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/landing_sandbox_fixed.png",
    });
  }

  // 0c. Pricing Page
  await page.goto("/pricing");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/pricing_page_fixed.png",
  });

  // 0d. Security Page
  await page.goto("/security");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/security_page_fixed.png",
  });

  // Direct login with cookie or login page
  await page.goto("/login");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/login_page_fixed.png",
  });
  await page.waitForLoadState("networkidle");

  const apiKeyInput = page.locator("#apiKey");
  await apiKeyInput.fill("pf_dev_adm_9901");
  await page.click("button[type='submit']");
  await page.waitForURL("**/overview", { timeout: 10000 }).catch(() => {});

  // 1. Orders page with enhanced metrics cards & clean layout
  await page.goto("/orders");
  await page.waitForSelector(".metrics-row");

  // Force Light mode first to capture the exact comparison with user's screenshot
  await page.evaluate(() => {
    document.documentElement.classList.remove("dark");
    localStorage.setItem("theme", "light");
    document.dispatchEvent(new Event("preflight:themechange"));
  });
  await page.waitForTimeout(400);

  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_orders_light.png",
  });

  // Open Upload Modal in Light Mode
  const uploadBtn = page.locator("button:has-text('Tải lên đơn hàng')").first();
  await uploadBtn.click();
  await page.waitForSelector(".upload-modal-v2");
  await page.waitForTimeout(400);
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_upload_modal_light.png",
  });

  // Close Upload Modal
  await page.locator("button[aria-label='Đóng cửa sổ']").click();
  await page.waitForTimeout(400);

  // Capture Reports in Light Mode
  await page.goto("/reports");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_reports_light.png",
  });
  await page.goto("/orders");
  await page.waitForSelector(".metrics-row");

  // Now switch to Dark Mode and capture
  await page.evaluate(() => {
    document.documentElement.classList.add("dark");
    localStorage.setItem("theme", "dark");
    document.dispatchEvent(new Event("preflight:themechange"));
  });
  await page.waitForTimeout(400);

  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_orders_dark.png",
  });

  await uploadBtn.click();
  await page.waitForSelector(".upload-modal-v2");
  await page.waitForTimeout(400);
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_upload_modal_dark.png",
  });
  await page.locator("button[aria-label='Đóng cửa sổ']").click();
  await page.waitForTimeout(400);

  // 3. Open Decision Modal
  const decisionBtn = page.locator("button:has-text('Xem xét & Duyệt đơn')").first();
  if (await decisionBtn.isVisible()) {
    await decisionBtn.click();
    await page.waitForSelector(".decision-modal");
    await page.screenshot({
      path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_decision_modal.png",
    });
    await page.click("button[aria-label='Đóng']");
    await page.waitForTimeout(300);
  }

  // 5. Audit Certificate
  await page.goto("/audit-certificate");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_certificate.png",
  });

  // 6. Reports
  await page.goto("/reports");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_reports.png",
  });

  // 7. Agent Graph
  await page.goto("/agent-graph");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_agent_graph.png",
  });

  // 8. RAG Playground
  await page.goto("/rag-playground");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_rag_playground.png",
  });

  // 9. ERP Sync Outbox
  await page.goto("/erp-sync");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_erp_sync.png",
  });

  // 10. Mobile Approval View (390 x 844)
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/m/orders/PO-10428");
  await page.waitForLoadState("networkidle");
  await page.screenshot({
    path: "/Users/huynhnguyen/.gemini/antigravity-ide/brain/1f94c309-a64a-4cae-829b-f5b25f423a4c/scratch/google_ui_mobile_order.png",
  });
});
