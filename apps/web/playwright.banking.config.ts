import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: "banking.spec.ts",
  workers: 1,
  reporter: "list",
  use: { baseURL: "http://127.0.0.1:5187", ...devices["Desktop Chrome"] },
  webServer: {
    command: "PREFLIGHT_DISABLE_INSPECTOR=1 npm run dev -- --hostname 127.0.0.1 --port 5187",
    url: "http://127.0.0.1:5187",
    reuseExistingServer: false,
    timeout: 120000,
  },
});
