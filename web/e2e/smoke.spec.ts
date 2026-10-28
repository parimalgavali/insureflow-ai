import { expect, test } from "@playwright/test";

// Scripted hit-and-run conversation replayed by the recorded LLM provider
// (tests/fixtures/agent/hit_and_run.json) through the real API, Postgres and pgvector.
const MSG1 =
  "Gestern Abend hat jemand mein geparktes Auto auf dem Supermarktparkplatz in Köln angefahren und ist einfach weggefahren. Die hintere Stoßstange ist eingedrückt.";
const MSG2 = "Das war am 25.10.2026 gegen 19 Uhr. Die Polizei habe ich nicht gerufen, Zeugen gab es keine.";

test("file a motor claim by conversation and send it to an adjuster", async ({ page }) => {
  await page.goto("/");
  const composer = page.getByLabel("Your message");
  await expect(composer).toBeEnabled();

  await composer.fill(MSG1);
  await composer.press("Enter");
  // agent asks a follow-up and offers chips for the missing facts
  await expect(page.getByLabel("Suggested answers")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByLabel("Claim card")).toContainText(/Köln/);

  await composer.fill(MSG2);
  await composer.press("Enter");

  const card = page.getByLabel("Claim card");
  await expect(card.getByTestId("coverage")).toBeVisible({ timeout: 60_000 });
  await expect(card.getByTestId("status")).toHaveText(/awaiting adjuster/i);
  for (const clause of ["A.2.2.2.2", "E.1.1.3", "E.1.1.1", "A.2.5.8"]) {
    await expect(card.getByRole("button", { name: `Show clause ${clause}` }).first()).toBeVisible();
  }
  await card.getByRole("button", { name: "Show clause E.1.1.3" }).first().click();
  await expect(card.getByTestId("popover")).toContainText(/Aufklärungspflicht/);
  await expect(card.getByTestId("risk")).toHaveText(/low|medium|high/);

  await card.getByTestId("review").click();
  await expect(card.getByTestId("status")).toHaveText(/reviewed/i);
  await expect(composer).toBeDisabled();
});
