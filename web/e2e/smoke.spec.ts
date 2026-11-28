import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";
import { adjusterToken } from "../playwright.config";

// Scripted hit-and-run conversation replayed by the recorded LLM provider
// (tests/fixtures/agent/policy_hit_and_run_followup.json) through the real API and scoped policy search.
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

  await expect(page.getByTestId("policy-source")).toContainText("standard GDV");
  await page.locator('#policy-file').setInputFiles('../tests/fixtures/sample_policy.pdf');
  await page.getByTestId("upload-policy").click();
  await expect(page.getByTestId("policy-filename")).toHaveText("sample_policy.pdf");
  await expect(page.getByTestId("policy-status")).toContainText("awaiting text preparation");
  await page.getByTestId("prepare-policy").click();
  await expect(page.getByTestId("policy-status")).toHaveText("Text prepared for searching", { timeout: 45_000 });
  await expect(page.getByTestId("policy-counts")).toContainText("3 pages");
  await expect(page.getByTestId("policy-source")).toContainText("Selected policy: sample_policy.pdf");

  // A rejected file returns the message to the draft; replace it with a real disk PDF.
  await page.locator('.chat input[type="file"]').setInputFiles({ name: "broken.png", mimeType: "image/png", buffer: Buffer.from("not an image") });
  await composer.fill(MSG1);
  await composer.press("Enter");
  await expect(page.getByRole("alert")).toContainText("back in the draft");
  await expect(composer).toBeEnabled();
  await expect(composer).toHaveValue(MSG1);
  await expect(page.getByRole("button", { name: "Retry", exact: true })).toHaveCount(0);
  await page.locator('.chat input[type="file"]').setInputFiles('../tests/fixtures/unreadable_claim.pdf');
  await page.getByLabel("What is this attachment?").selectOption("police_report");
  await composer.press("Enter");
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.getByTestId("evidence-list")).toContainText("Police report");
  await expect(page.getByTestId("fact-photos_attached")).toHaveText("no");
  // agent asks a follow-up and offers chips for the missing facts
  await expect(page.getByLabel("Suggested answers")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByLabel("Claim card")).toContainText(/Köln/);
  await expect(page.getByTestId("risk-insufficient")).toHaveText("Not enough information");
  await expect(page.getByTestId("risk-missing")).toContainText("Police informed");
  await expect(page.getByTestId("risk")).toHaveCount(0);

  const savedId = await page.evaluate(() => localStorage.getItem("claimpilot_conversation_id"));
  const firstConversation = await (await page.request.get(`/api/conversations/${savedId}`)).json();
  const unreadableId = firstConversation.attachments[0].id;
  const unreadable = page.getByTestId(`attachment-${unreadableId}`);
  await unreadable.getByRole("button", { name: "Read claim PDF" }).click();
  await expect(unreadable).toContainText("no selectable text");
  await expect(unreadable).toContainText("scans are not read automatically");
  await expect(page.getByTestId("evidence-suggestion")).toHaveCount(0);
  await unreadable.getByRole("button", { name: "Enter details yourself" }).click();
  await expect(page.getByLabel("Date", { exact: true })).toBeFocused();
  await page.getByRole("button", { name: "Cancel edits", exact: true }).click();
  await unreadable.getByRole("button", { name: "Replace PDF copy" }).click();
  await unreadable.getByLabel("Choose a clearer PDF copy").setInputFiles({ name: "clear-report.pdf", mimeType: "application/pdf", buffer: readFileSync('../tests/fixtures/claim_evidence.pdf') });
  await expect(unreadable).toContainText("Replace unreadable_claim.pdf with clear-report.pdf?");
  await page.route("**/api/conversations/*/attachments/*", async (route) => {
    if (route.request().method() !== "PUT") return route.continue();
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    await route.fulfill({ response, body: "{" });
  }, { times: 1 });
  await unreadable.getByRole("button", { name: "Save replacement copy" }).click();
  await expect(page.getByRole("alert")).toContainText("Retry with the same copy");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(unreadable).toContainText("Previous copy");
  await expect(unreadable.getByRole("button")).toHaveCount(0);
  await expect(page.getByTestId("evidence-list")).toContainText("clear-report.pdf");
  await expect(page.getByTestId("evidence-list")).toContainText("Version 2");
  await expect(page.locator('[data-history-kind="evidence_replaced"]')).toHaveCount(1);
  await page.reload();
  await expect(composer).toBeEnabled();
  await expect(page.getByRole("log")).toContainText(MSG1);
  await expect(page.getByTestId("policy-status")).toHaveText("Text prepared for searching");
  await expect(page.getByTestId("policy-filename")).toHaveText("sample_policy.pdf");
  await expect(page.getByTestId("evidence-list")).toContainText("Police report");
  expect(await page.evaluate(() => localStorage.getItem("claimpilot_conversation_id"))).toBe(savedId);

  // Lose the terminal response after a message with a file has been saved.
  let savedConversationUrl = "";
  await page.route("**/api/conversations/*/messages", async (route) => {
    savedConversationUrl = route.request().url().replace(/\/messages$/, "");
    const response = await route.fetch();
    const body = await response.text();
    expect(response.status(), body).toBe(200);
    await route.fulfill({ response, body: body.slice(0, body.lastIndexOf("event: done")) });
  }, { times: 1 });
  // Use in-memory bytes because intercepted native file paths are omitted by CDP post data.
  await page.locator('.chat input[type="file"]').setInputFiles({ name: "claim.pdf", mimeType: "application/pdf", buffer: readFileSync('../tests/fixtures/claim_evidence.pdf') });
  await page.getByLabel("What is this attachment?").selectOption("repair_estimate");
  await composer.fill(MSG2);
  await composer.press("Enter");
  await expect(page.getByRole("alert")).toContainText("same text and attachment", { timeout: 60_000 });
  await expect(page.getByTestId("evidence-list")).toContainText("claim.pdf");
  await expect(page.getByTestId("evidence-list")).toContainText("Repair estimate");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  const canonical = await (await page.request.get(savedConversationUrl)).json();
  expect(canonical.messages.filter((m: { content: string }) => m.content.startsWith(MSG2))).toHaveLength(1);

  const card = page.getByLabel("Claim card");
  await expect(card.getByTestId("fact-photos_attached")).toHaveText("no");
  await expect(card.getByTestId("evidence-list")).toContainText("Not yet analysed for claim details");
  expect(canonical.attachments).toHaveLength(3);
  const evidenceId = canonical.attachments.find((a: { filename: string }) => a.filename === "claim.pdf").id;
  const estimateRequestId = canonical.document_checklist.find((item: { document_type: string; origin: string }) => item.document_type === "repair_estimate" && item.origin === "assessment").id;
  await expect(card.getByTestId(`document-state-${estimateRequestId}`)).toHaveText("Uploaded — awaiting reviewer check");
  // Lose the extraction response after it is committed; retry reuses saved suggestions.
  await page.route("**/api/conversations/*/attachments/*/extract", async (route) => {
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    await route.fulfill({ response, body: "{" });
  }, { times: 1 });
  await card.getByTestId(`extract-evidence-${evidenceId}`).click();
  await expect(page.getByRole("alert")).toContainText("finish reading this PDF");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(card.getByTestId("evidence-suggestion")).toHaveCount(2);
  await expect(card.getByTestId("evidence-list")).toContainText("claim.pdf · page 1");
  await expect(card.getByTestId("evidence-list")).toContainText("Repair estimate: EUR 1200.00");
  await expect(card.getByTestId("fact-estimated_amount_eur")).toHaveText("—");
  await expect(card.getByTestId("coverage")).toBeVisible({ timeout: 60_000 });
  await expect(card.getByTestId("status")).toHaveText(/ready to submit/i);
  await expect(card.getByTestId("coverage-source")).toContainText("sample_policy.pdf");
  for (const passage of ["P.1", "P.2", "P.3"]) {
    await expect(card.getByRole("button", { name: `Show passage ${passage} from sample_policy.pdf` }).first()).toBeVisible();
  }
  await card.getByRole("button", { name: "Show passage P.3 from sample_policy.pdf" }).first().click();
  await expect(card.getByTestId("popover")).toContainText("notify the insurer within one week");
  await expect(card.getByTestId("popover")).toContainText("page 3");
  await expect(card.getByTestId("risk")).toHaveText(/low|medium|high/);

  await page.reload();
  await expect(page.getByTestId("evidence-suggestion")).toHaveCount(2);
  await expect(card.getByTestId("fact-estimated_amount_eur")).toHaveText("—");
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

  // Compare document suggestions with confirmed facts and decide each separately.
  const amountSuggestion = card.getByTestId("evidence-suggestion").filter({ hasText: "Estimated amount (EUR)" });
  const dateSuggestion = card.getByTestId("evidence-suggestion").filter({ hasText: "Date" });
  await expect(amountSuggestion).toContainText("Saved value: 900");
  await expect(amountSuggestion).toContainText("Document suggestion: 1200");
  await expect(amountSuggestion.getByRole("button", { name: "Accept suggestion" })).toBeDisabled();
  await dateSuggestion.getByRole("button", { name: "Reject suggestion" }).click();
  await expect(dateSuggestion).toContainText("Rejected.");
  await expect(card.getByTestId("fact-incident_date")).toHaveText("2026-10-25");
  await amountSuggestion.getByLabel("Replace the saved value with this suggestion.").check();
  // The decision is saved even when its response is lost; finish replays it once.
  await page.route("**/api/claims/*/evidence-suggestions/*/decision", async (route) => {
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    await route.fulfill({ response, body: "{" });
  }, { times: 1 });
  await amountSuggestion.getByRole("button", { name: "Accept suggestion" }).click();
  await expect(page.getByRole("alert")).toContainText("document decision could not be completed");
  await page.getByRole("button", { name: "Finish document decision", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(amountSuggestion).toContainText("Accepted earlier");
  await expect(card.getByTestId("fact-estimated_amount_eur")).toHaveText("1200");
  await expect(card.getByTestId("assessment-stale")).toHaveCount(0);
  await expect(page.locator('[data-history-kind="evidence_accepted"]')).toHaveCount(1);
  await expect(page.locator('[data-history-kind="evidence_rejected"]')).toHaveCount(1);

  // Confirm a replacement, prepare it, and refresh before submission.
  await page.getByTestId("replace-policy").click();
  await page.locator('#policy-file').setInputFiles('../tests/fixtures/replacement_policy.pdf');
  await expect(page.getByTestId("replacement-confirmation")).toContainText("Replace sample_policy.pdf with replacement_policy.pdf?");
  await page.getByTestId("upload-policy").click();
  await expect(page.getByTestId("policy-filename")).toHaveText("replacement_policy.pdf");
  await expect(page.getByTestId("policy-revision")).toHaveText("Version 2");
  await expect(card.getByTestId("assessment-stale")).toBeVisible();
  await expect(card.getByTestId("submit")).toBeDisabled();
  await page.getByTestId("prepare-policy").click();
  await expect(page.getByTestId("policy-status")).toHaveText("Text prepared for searching");
  await expect(card.getByTestId("assessment-stale")).toBeVisible();
  await card.getByTestId("customer-refresh").click();
  await expect(card.getByTestId("assessment-stale")).toHaveCount(0);
  await expect(card.getByTestId("coverage-source")).toContainText("replacement_policy.pdf");
  await card.getByRole("button", { name: "Show passage P.2 from replacement_policy.pdf" }).first().click();
  await expect(card.getByTestId("popover")).toContainText("EUR 500");

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
  await expect(reviewCard.getByTestId("evidence-list")).toContainText("Repair estimate");
  await expect(reviewCard.getByTestId("evidence-list")).toContainText("claim.pdf");
  await expect(reviewCard.getByTestId("evidence-suggestion")).toHaveCount(2);
  await expect(reviewCard.getByTestId("risk")).toHaveText(/low|medium|high/);
  await expect(reviewCard.getByTestId("summary")).toContainText(/P\.1/);
  const estimateRequest = reviewCard.getByTestId(`document-item-${estimateRequestId}`);
  await estimateRequest.getByRole("button", { name: "Confirm after checking documents" }).click();
  await expect(reviewCard.getByTestId(`document-state-${estimateRequestId}`)).toHaveText("Confirmed by reviewer");
  // Ask for more information rather than completing the review.
  await reviewCard.getByLabel("What information does the customer need to provide?").fill("Please provide the police report and repair estimate.");
  await reviewCard.getByRole("checkbox", { name: "Repair estimate", exact: true }).check();
  await reviewCard.getByRole("checkbox", { name: "Police report", exact: true }).check();
  await reviewCard.getByTestId("request-info").click();
  await expect(reviewCard.getByTestId("status")).toHaveText("Information needed");
  await expect(row).toHaveCount(0);
  await page.getByRole("button", { name: "Lock queue" }).click();
  await page.getByTestId("reviewer-link").click();
  await expect(page.getByTestId("information-request")).toContainText("police report and repair estimate");
  const requestedAgain = await (await page.request.get(savedConversationUrl)).json();
  const newEstimateRequestId = requestedAgain.document_checklist.find((item: { document_type: string; origin: string }) => item.document_type === "repair_estimate" && item.origin === "reviewer").id;
  const newEstimateRequest = page.getByTestId(`document-item-${newEstimateRequestId}`);
  await expect(page.getByTestId(`document-state-${newEstimateRequestId}`)).toHaveText("Missing");
  await newEstimateRequest.getByLabel("Link an uploaded file").selectOption(evidenceId);
  await newEstimateRequest.getByRole("button", { name: "Link file", exact: true }).click();
  await expect(page.getByTestId(`document-state-${newEstimateRequestId}`)).toHaveText("Uploaded — awaiting reviewer check");
  await page.reload();
  await expect(page.getByTestId(`document-state-${newEstimateRequestId}`)).toHaveText("Uploaded — awaiting reviewer check");
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
  await page.getByTestId(`document-item-${newEstimateRequestId}`).getByRole("button", { name: "Confirm after checking documents" }).click();
  await expect(page.getByTestId(`document-state-${newEstimateRequestId}`)).toHaveText("Confirmed by reviewer");
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
  await expect(page.getByTestId("history-event")).toHaveCount(17);
  await page.getByTestId("saved-history-link").click();
  await expect(page.getByTestId("claim-history")).toContainText("Checked the updated claim details.");
  await expect(page.getByTestId("claim-history")).toContainText("Reviewer (shared demo access)");
  await page.reload();
  await expect(page.getByTestId("history-event")).toHaveCount(17);
  await expect(page.getByTestId("claim-history")).toContainText("Checked the updated claim details.");
  await page.goto("/");
  await expect(page.getByLabel("Claim card").getByTestId("status")).toHaveText(/reviewed/i);
  await page.getByTestId("new-claim").click();
  await expect(page.getByLabel("Claim card").getByTestId("status")).toHaveText("Collecting facts");
  expect(await page.evaluate(() => localStorage.getItem("claimpilot_conversation_id"))).not.toBe(savedId);
  const oldClaim = await (await page.request.get(savedConversationUrl)).json();
  expect(oldClaim.status).toBe("reviewed");
  expect(oldClaim.history).toHaveLength(17);

});
