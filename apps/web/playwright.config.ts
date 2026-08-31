import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  use: { baseURL: "http://127.0.0.1:3100", trace: "retain-on-failure" },
  webServer: [
    { command: "PYTHONPATH=../../packages/core ../../.venv/bin/python -m learning_manager.api.stub --port 8011", url: "http://127.0.0.1:8011/docs", reuseExistingServer: false, timeout: 120000 },
    { command: "API_ORIGIN=http://127.0.0.1:8011 npm run dev -- --port 3100", url: "http://127.0.0.1:3100", reuseExistingServer: false, timeout: 120000 },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
