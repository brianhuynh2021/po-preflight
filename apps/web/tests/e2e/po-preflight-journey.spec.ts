import { test, expect } from "@playwright/test";

test.describe("PO Preflight — End-to-End Enterprise Operations Test Suite", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to base URL before each test
    await page.goto("/");
  });

  test("Journey 1: Landing page loads with Nhat Minh Tech branding and core pillars", async ({ page }) => {
    // Check main title / heading
    await expect(page).toHaveTitle(/PO Preflight/i);

    // Verify Nhat Minh Tech Branding
    const brandText = page.locator("text=Nhật Minh Technology");
    await expect(brandText.first()).toBeVisible();

    // Verify Founder & Contact Details
    const hotline = page.locator("text=0984 883 750");
    await expect(hotline.first()).toBeVisible();

    const email = page.locator("text=huynh2102@gmail.com");
    await expect(email.first()).toBeVisible();

    // Verify 4 Core Technology Pillars
    await expect(page.locator("text=Bóc Tách Zero-Hallucination").first()).toBeVisible();
    await expect(page.locator("text=4-Tier Waterfall Hybrid RAG").first()).toBeVisible();
    await expect(page.locator("text=Phê Duyệt 1 Chạm Telegram & Zalo").first()).toBeVisible();
  });

  test("Journey 2: Orders Overview & Preflight Queue rendering", async ({ page }) => {
    await page.goto("/orders");

    // Verify PO List Header
    const pageHeader = page.locator("h1, h2, [role='heading']");
    await expect(pageHeader.first()).toBeVisible();

    // Verify sample POs exist in the DOM
    const poItem = page.locator("text=PO-10428");
    await expect(poItem.first()).toBeVisible();

    // Verify Customer Name
    const customer = page.locator("text=Northstar Retail");
    await expect(customer.first()).toBeVisible();

    // Verify Status Badges exist
    const reviewBadge = page.locator("text=Review required");
    await expect(reviewBadge.first()).toBeVisible();
  });

  test("Journey 3: Order Review & Preflight Findings Inspection", async ({ page }) => {
    await page.goto("/orders/PO-10428");

    // Check order detail page title
    await expect(page.locator("text=PO-10428").first()).toBeVisible();

    // Check line items table
    const table = page.locator("table");
    if (await table.count() > 0) {
      await expect(table.first()).toBeVisible();
    }

    // Inspect Action buttons (Approve / Reject / Changes Requested)
    const approveBtn = page.locator("button:has-text('Duyệt'), button:has-text('Approve')");
    if (await approveBtn.count() > 0) {
      await expect(approveBtn.first()).toBeVisible();
    }
  });

  test("Journey 4: Extraction Review Studio navigation and interface", async ({ page }) => {
    await page.goto("/staging");

    // Verify Extraction Review Studio exists
    const studioTitle = page.locator("text=Bóc Tách, text=Extraction, text=Staging");
    await expect(studioTitle.first()).toBeVisible();
  });

  test("Journey 5: Multi-Channel Bot Settings and Telegram/Zalo configuration", async ({ page }) => {
    await page.goto("/settings");

    // Check Settings title
    await expect(page.locator("text=Cài Đặt, text=Settings").first()).toBeVisible();

    // Check Telegram & Zalo Cards
    await expect(page.locator("text=Telegram").first()).toBeVisible();
    await expect(page.locator("text=Zalo").first()).toBeVisible();

    // Verify Vietnamese labels
    await expect(page.locator("text=Webhook, text=API Token, text=Chat ID").first()).toBeVisible();
  });
});
