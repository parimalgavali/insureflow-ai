import { expect, test, type Page } from "@playwright/test";
import { adjusterToken } from "../playwright.config";

// Scripted hit-and-run conversation replayed by the recorded LLM provider
// (tests/fixtures/agent/hit_and_run.json) through the real API, Postgres and pgvector.
const MSG1 =
  "Gestern Abend hat jemand mein geparktes Auto auf dem Supermarktparkplatz in Köln angefahren und ist einfach weggefahren. Die hintere Stoßstange ist eingedrückt.";
const MSG2 = "Das war am 25.10.2026 gegen 19 Uhr. Die Polizei habe ich nicht gerufen, Zeugen gab es keine.";

async function findQueuedClaim(page: Page, claimId: string) {
  const row = page.getByTestId(`review-claim-${claimId}`);
  const refresh = page.getByRole("button", { name: "Refresh list" });
  await expect(refresh).toBeEnabled();
  for (let pageNumber = 0; pageNumber < 100 && !(await row.count()); pageNumber++) {
    const more = page.getByRole("button", { name: "Load more" });
    if (!(await more.isVisible())) break;
    await more.click();
    await expect(refresh).toBeEnabled();
  }
  await expect(row).toBeVisible();
  return row;
}

test("file a motor claim by conversation and send it to an adjuster", async ({ page }) => {
  await page.goto("/");
  // English UI by default (headless Chromium reports en-US); switch to German and back to prove the toggle
  await expect(page.getByLabel("Your message")).toBeEnabled();
  await page.getByTestId("lang-de").click();
  await expect(page.getByRole("heading", { name: "Schadenkarte" })).toBeVisible();
  await expect(page.getByRole("log")).toContainText(/Hallo! Ich bin ClaimPilot/);
  await page.getByTestId("lang-en").click();
  await expect(page.getByRole("heading", { name: "Claim card" })).toBeVisible();
  const composer = page.getByLabel("Your message");
  await expect(composer).toBeEnabled();

  await composer.fill(MSG1);
  await composer.press("Enter");
  // agent asks a follow-up and offers chips for the missing facts
  await expect(page.getByLabel("Suggested answers")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByLabel("Claim card")).toContainText(/Köln/);
  await expect(page.getByTestId("risk-insufficient")).toHaveText("Not enough information");
  await expect(page.getByTestId("risk-missing")).toContainText("Police informed");
  await expect(page.getByTestId("risk")).toHaveCount(0);

  const savedId = await page.evaluate(() => localStorage.getItem("claimpilot_conversation_id"));
  await page.reload();
  await expect(composer).toBeEnabled();
  await expect(page.getByRole("log")).toContainText(MSG1);
  expect(await page.evaluate(() => localStorage.getItem("claimpilot_conversation_id"))).toBe(savedId);

  // Lose the terminal response after a message with a file has been saved.
  let savedConversationUrl = "";
  await page.route("**/api/conversations/*/messages", async (route) => {
    savedConversationUrl = route.request().url().replace(/\/messages$/, "");
    const response = await route.fetch();
    const body = await response.text();
    await route.fulfill({ response, body: body.slice(0, body.lastIndexOf("event: done")) });
  }, { times: 1 });
  await page.locator('input[type="file"]').setInputFiles({ name: "claim.pdf", mimeType: "application/pdf", buffer: Buffer.from("Sample claim document") });
  await composer.fill(MSG2);
  await composer.press("Enter");
  await expect(page.getByRole("alert")).toContainText("same text and attachment", { timeout: 60_000 });
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  const canonical = await (await page.request.get(savedConversationUrl)).json();
  expect(canonical.messages.filter((m: { content: string }) => m.content.startsWith(MSG2))).toHaveLength(1);

  const card = page.getByLabel("Claim card");
  await expect(card.getByTestId("coverage")).toBeVisible({ timeout: 60_000 });
  await expect(card.getByTestId("status")).toHaveText(/ready to submit/i);
  for (const clause of ["A.2.2.2.2", "E.1.1.3", "E.1.1.1", "A.2.5.8"]) {
    await expect(card.getByRole("button", { name: `Show clause ${clause}` }).first()).toBeVisible();
  }
  await card.getByRole("button", { name: "Show clause E.1.1.3" }).first().click();
  await expect(card.getByTestId("popover")).toContainText(/Aufklärungspflicht/);
  await expect(card.getByTestId("risk")).toHaveText(/low|medium|high/);

  // The customer can correct facts before submitting and sees simple validation.
  await card.getByTestId("edit-customer-facts").click();
  await page.getByLabel("Date", { exact: true }).fill("2026-02-30");
  await expect(page.getByRole("alert")).toContainText("real date");
  await expect(card.getByTestId("save-customer-facts")).toBeDisabled();
  await page.getByLabel("Date", { exact: true }).fill("2026-10-25");
  await page.getByLabel("Estimated amount (EUR)", { exact: true }).fill("-10");
  await expect(page.getByRole("alert")).toContainText("zero or more");
  await page.getByLabel("Estimated amount (EUR)", { exact: true }).fill("900");
  await card.getByTestId("save-customer-facts").click();
  await expect(card.getByTestId("fact-estimated_amount_eur")).toHaveText("900");
  await expect(card.getByTestId("status")).toHaveText("Ready to submit");

  // Customer submission never prompts for adjuster credentials or completes a review.
  await expect(card.getByTestId("review")).toHaveCount(0);
  const submission = page.waitForResponse((r) => r.url().endsWith("/submit") && r.request().method() === "POST");
  await card.getByTestId("submit").click();
  const submitted = await (await submission).json();
  await expect(card.getByTestId("status")).toHaveText(/awaiting adjuster/i);
  await expect(card.getByTestId("submit")).toHaveCount(0);
  await expect(composer).toBeDisabled();

  // Reviewer actions live on a separate protected screen.
  await expect(card.getByTestId("review")).toHaveCount(0);
  await page.getByTestId("reviewer-link").click();
  await page.getByLabel("Reviewer token").fill("wrong-token");
  await page.getByRole("button", { name: "Open queue" }).click();
  await expect(page.getByRole("alert")).toContainText(/403/);
  await page.getByLabel("Reviewer token").fill(adjusterToken);
  await page.getByRole("button", { name: "Open queue" }).click();
  const row = await findQueuedClaim(page, submitted.id);
  await expect(row).toContainText("Submitted:");
  await row.click();
  const reviewCard = page.getByLabel("Claim card");
  await expect(reviewCard.getByTestId("risk")).toHaveText(/low|medium|high/);
  await expect(reviewCard.getByTestId("summary")).toContainText(/A\.2\.2/);
  // Ask for more information rather than completing the review.
  await reviewCard.getByLabel("What information does the customer need to provide?").fill("Please provide the police report and repair estimate.");
  await reviewCard.getByTestId("request-info").click();
  await expect(reviewCard.getByTestId("status")).toHaveText("Information needed");
  await expect(row).toHaveCount(0);
  await page.getByRole("button", { name: "Lock queue" }).click();
  await page.getByTestId("reviewer-link").click();
  await expect(page.getByTestId("information-request")).toContainText("police report and repair estimate");
  await page.reload();
  await expect(page.getByTestId("information-request")).toContainText("police report and repair estimate");
  await expect(composer).toBeEnabled();
  await composer.fill("The police have now been informed. The repair estimate is 1200 Euro.");
  await composer.press("Enter");
  await expect(page.getByLabel("Claim card").getByTestId("status")).toHaveText("Ready to submit");
  await page.getByTestId("submit").click();
  await expect(page.getByLabel("Claim card").getByTestId("status")).toHaveText(/awaiting adjuster/i);
  await page.getByTestId("reviewer-link").click();
  await page.getByLabel("Reviewer token").fill(adjusterToken);
  await page.getByRole("button", { name: "Open queue" }).click();
  await (await findQueuedClaim(page, submitted.id)).click();
  await expect(page.getByTestId("fact-estimated_amount_eur")).toHaveText("1200");
  await page.getByRole("button", { name: "Edit facts", exact: true }).click();
  await page.getByLabel("Witnesses", { exact: true }).fill("maybe");
  await page.getByRole("button", { name: "Save corrections and refresh" }).click();
  await expect(page.getByRole("alert")).toContainText("correction is not valid");
  await page.getByLabel("Witnesses", { exact: true }).fill("yes");
  await page.getByRole("button", { name: "Save corrections and refresh" }).click();
  await expect(page.getByTestId("correction-witnesses")).toContainText("no → yes");
  await expect(reviewCard.getByTestId("status")).toHaveText(/awaiting adjuster/i);
  await expect(page.getByTestId("fact-witnesses")).toHaveText("yes");
  await expect(page.getByTestId("assessment-stale")).toHaveCount(0);
  await page.getByLabel("Review note (optional)").fill("Checked the updated claim details.");
  await page.getByLabel("Claim card").getByTestId("review").click();
  await expect(reviewCard.getByTestId("status")).toHaveText(/reviewed/i);
  await expect(row).toHaveCount(0);
  await page.getByRole("button", { name: "Lock queue" }).click();
  await expect(page.getByLabel("Reviewer token")).toBeVisible();
  await expect(page.getByLabel("Claim card")).toHaveCount(0);
  await page.getByTestId("reviewer-link").click();
  await expect(page.getByLabel("Claim card").getByTestId("status")).toHaveText(/reviewed/i);
  await expect(page.getByTestId("history-event")).toHaveCount(8);
  await page.getByTestId("saved-history-link").click();
  await expect(page.getByTestId("claim-history")).toContainText("Checked the updated claim details.");
  await expect(page.getByTestId("claim-history")).toContainText("Reviewer (shared demo access)");
  await page.reload();
  await expect(page.getByTestId("history-event")).toHaveCount(8);
  await expect(page.getByTestId("claim-history")).toContainText("Checked the updated claim details.");
  await page.goto("/");
  await expect(page.getByLabel("Claim card").getByTestId("status")).toHaveText(/reviewed/i);
  await page.getByTestId("new-claim").click();
  await expect(page.getByLabel("Claim card").getByTestId("status")).toHaveText("Collecting facts");
  expect(await page.evaluate(() => localStorage.getItem("claimpilot_conversation_id"))).not.toBe(savedId);
  const oldClaim = await (await page.request.get(savedConversationUrl)).json();
  expect(oldClaim.status).toBe("reviewed");
  expect(oldClaim.history).toHaveLength(8);

});
