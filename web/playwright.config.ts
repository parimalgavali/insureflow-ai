import { defineConfig } from "@playwright/test";

// Smoke test against the real API (recorded LLM responses, real Postgres/pgvector).
// `npm run e2e` starts both servers; set E2E_API_URL to reuse a running API instead.
const apiPort = 8000;
const webPort = 5173;

export default defineConfig({
  testDir: "e2e",
  timeout: 90_000,
  retries: 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: { baseURL: `http://localhost:${webPort}`, trace: "retain-on-failure" },
  webServer: [
    {
      command: `cd .. && LLM_PROVIDER=recorded uv run uvicorn api.main:app --port ${apiPort}`,
      url: `http://localhost:${apiPort}/api/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: `npm run dev -- --port ${webPort} --strictPort`,
      url: `http://localhost:${webPort}`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
