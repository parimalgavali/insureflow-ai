import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ClaimCard from "../src/components/ClaimCard.vue";

const citation = { clause_id: "A.2.2.2.2", title: "Unfall", excerpt: "Versichert sind Schäden durch Unfall.", page: 11, score: 0.8 };
const facts = {
  incident_date: null, incident_time: null, location: "Köln", event_type: "hit_and_run", description: null,
  third_party_involved: true, third_party_known: false, injuries: null, police_report_filed: null, witnesses: null,
  damage_description: "Stoßstange", estimated_amount_eur: null, vehicle_drivable: null, photos_attached: false,
};
const card = {
  facts: { ...facts, incident_date: "2026-10-25" },
  policy: { product: "vollkasko" as const, deductible_eur: 300 },
  coverage_status: "likely_covered" as const,
  coverage_summary: "Nach den Musterbedingungen versichert [A.2.2.2.2]. Pflichten beachten [E.1.1.1].",
  citations: [citation, { clause_id: "E.1.1.1", title: "Anzeigepflicht", excerpt: "Innerhalb einer Woche.", page: 31, score: 0.7 }],
  risk: { score: 0.42, band: "medium" as const, reasons: ["no police report", "no witnesses", "evening"], model_version: "v1" },
  cost: { claims_per_year: 0.1, claim_eur: 1900, annual_cost_eur: 190, portfolio_claim_eur: 1864, basis: "freMTPL2" },
  missing_documents: ["Fotos"],
  next_steps: ["Fotos hochladen", "Prüfung durch Sachbearbeiter"],
  status: "awaiting_review" as const,
  review: null,
};

describe("ClaimCard", () => {
  it("shows missing facts while collecting", () => {
    const w = mount(ClaimCard, { props: { facts, missing: ["incident_date"], citations: [], risk: null, card: null, status: "collecting", busy: false } });
    expect(w.get('[data-testid="fact-incident_date"]').text()).toBe("missing");
    expect(w.get('[data-testid="fact-location"]').text()).toBe("Köln");
    expect(w.get('[data-testid="status"]').text()).toBe("Collecting facts");
    expect(w.find('[data-testid="review"]').exists()).toBe(false);
    expect(w.find('[data-testid="submit"]').exists()).toBe(false);
  });

  it("renders citation pills inside the summary and opens a popover", async () => {
    const w = mount(ClaimCard, { props: { facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card, status: "awaiting_review", busy: false } });
    expect(w.get('[data-testid="coverage"]').text()).toBe("Likely covered");
    const pills = w.get('[data-testid="summary"]').findAll("button.pill");
    expect(pills.map((p) => p.text())).toEqual(["A.2.2.2.2", "E.1.1.1"]);
    expect(w.find('[data-testid="popover"]').exists()).toBe(false);
    await pills[0].trigger("click");
    expect(w.get('[data-testid="popover"]').text()).toContain("Versichert sind Schäden durch Unfall.");
    expect(pills[0].attributes("aria-pressed")).toBe("true");
    await pills[0].trigger("click");
    expect(w.find('[data-testid="popover"]').exists()).toBe(false);
    expect(w.get('[data-testid="risk"]').text()).toBe("medium");
    expect(w.findAll(".reasons li")).toHaveLength(3);
  });

  it("emits review with an accept decision, and a patch when facts were edited", async () => {
    const w = mount(ClaimCard, { props: { reviewer: true, facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card, status: "awaiting_review", busy: false } });
    await w.get('[data-testid="review"]').trigger("click");
    expect(w.emitted("review")?.[0]).toEqual([{}]);
    await w.get("button.btn:not(.primary)").trigger("click"); // Edit facts
    await w.get('input[aria-label="Witnesses"]').setValue("yes");
    await w.get('[data-testid="review"]').trigger("click");
    expect(w.emitted("review")?.[1]).toEqual([{ witnesses: true }]);
  });

  it("shows the reviewed badge", () => {
    const w = mount(ClaimCard, { props: { facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card: { ...card, status: "reviewed", review: { decision: "accept", note: "ok" } }, status: "reviewed", busy: false } });
    expect(w.get('[data-testid="status"]').text()).toBe("Reviewed");
    expect(w.text()).toContain("Reviewed by adjuster");
  });
});

it("shows the expected-cost context as context only", () => {
  const w = mount(ClaimCard, { props: { facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card, status: "awaiting_review", busy: false } });
  expect(w.get('[data-testid="cost"]').text()).toMatch(/1,900/);
  expect(w.get('[data-testid="cost"]').text()).toMatch(/context only/);
});

it("submits a ready claim without emitting a review or asking for credentials", async () => {
  const w = mount(ClaimCard, { props: { facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card: { ...card, status: "assessed" }, status: "assessed", busy: false } });
  expect(w.get('[data-testid="status"]').text()).toBe("Ready to submit");
  expect(w.find('[data-testid="review"]').exists()).toBe(false);
  await w.get('[data-testid="submit"]').trigger("click");
  expect(w.emitted("submit")).toHaveLength(1);
  expect(w.emitted("review")).toBeUndefined();
  await w.setProps({ busy: true });
  expect((w.get('[data-testid="submit"]').element as HTMLButtonElement).disabled).toBe(true);
  await w.setProps({ busy: false, status: "awaiting_review", card });
  expect(w.find('[data-testid="submit"]').exists()).toBe(false);
  expect(w.text()).toContain("waiting for an adjuster");
  expect(w.find('[data-testid="review"]').exists()).toBe(false);
  await w.setProps({ reviewer: true });
  expect(w.get('[data-testid="review"]').text()).toBe("Record adjuster review");
});

it("requires a clear information request and keeps it separate from a final review", async () => {
  const w = mount(ClaimCard, { props: { facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card, status: "awaiting_review", busy: false, reviewer: true } });
  expect((w.get('[data-testid="request-info"]').element as HTMLButtonElement).disabled).toBe(true);
  await w.get("textarea").setValue("   ");
  expect((w.get('[data-testid="request-info"]').element as HTMLButtonElement).disabled).toBe(true);
  await w.get("textarea").setValue("  Please provide the police report.  ");
  await w.get("form.request-info").trigger("submit");
  expect(w.emitted("requestInfo")?.[0]).toEqual(["Please provide the police report."]);
  expect(w.emitted("review")).toBeUndefined();
  await w.setProps({ status: "information_needed", reviewer: false, card: { ...card, status: "information_needed", review: { decision: "request_info", note: "Please provide the police report." } } });
  expect(w.get('[data-testid="status"]').text()).toBe("Information needed");
  expect(w.get('[data-testid="information-request"]').text()).toContain("police report");
  expect(w.text()).toContain("Reply in the chat");
  expect(w.find('[data-testid="review"]').exists()).toBe(false);
  expect(w.find('[data-testid="submit"]').exists()).toBe(false);
  expect(w.find("form.request-info").exists()).toBe(false);
});

it("labels failed guidance as out of date and blocks completion until it is refreshed", async () => {
  const stale = { ...card, assessment_stale: true, assessment_error: "The assessment could not be refreshed.", corrections: [{ field: "witnesses", before: false, after: true }] };
  const w = mount(ClaimCard, { props: { facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card: stale, status: "awaiting_review", busy: false, reviewer: true } });
  expect(w.get('[data-testid="assessment-stale"]').text()).toContain("Out of date");
  expect(w.get('[data-testid="coverage"]').text()).toBe("Out of date");
  expect(w.get('[data-testid="risk"]').text()).toBe("Out of date");
  expect(w.get('[data-testid="correction-witnesses"]').text()).toContain("no → yes");
  expect((w.get('[data-testid="review"]').element as HTMLButtonElement).disabled).toBe(true);
  await w.get('[data-testid="reassess"]').trigger("click");
  expect(w.emitted("reassess")).toHaveLength(1);
  expect(w.emitted("review")).toBeUndefined();
  await w.setProps({ card: { ...stale, assessment_stale: false, assessment_error: null } });
  expect(w.find('[data-testid="assessment-stale"]').exists()).toBe(false);
  expect((w.get('[data-testid="review"]').element as HTMLButtonElement).disabled).toBe(false);
});

it("keeps correction drafts until saved and does not turn invalid amounts into null", async () => {
  const w = mount(ClaimCard, { props: { facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card, status: "awaiting_review", busy: false, reviewer: true } });
  await w.findAll("button").find((b) => b.text() === "Edit facts")!.trigger("click");
  expect(w.get('[data-testid="review"]').text()).toBe("Save corrections and refresh");
  await w.get('input[aria-label="Estimated amount (EUR)"]').setValue("not an amount");
  await w.get('[data-testid="review"]').trigger("click");
  expect(w.emitted("review")?.[0]).toEqual([{ estimated_amount_eur: "not an amount" }]);
  expect(w.find('input[aria-label="Estimated amount (EUR)"]').exists()).toBe(true);
  expect(w.find("form.request-info").exists()).toBe(false);
  await w.findAll("button").find((b) => b.text() === "Cancel edits")!.trigger("click");
  expect(w.get('[data-testid="review"]').text()).toBe("Record adjuster review");
  expect(w.find("form.request-info").exists()).toBe(true);
});

it("lets a reviewer attach an optional note to a completed review", async () => {
  const w = mount(ClaimCard, { props: { facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card, status: "awaiting_review", busy: false, reviewer: true, claimId: "claim-1", history: [] } });
  await w.get("#review-note").setValue("  Checked the updated details.  ");
  await w.get('[data-testid="review"]').trigger("click");
  expect(w.emitted("review")?.[0]).toEqual([{}, "Checked the updated details."]);
  expect(w.get('[data-testid="saved-history-link"]').attributes("href")).toBe("#history/claim-1");
});
