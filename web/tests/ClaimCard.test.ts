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
    expect((w.get('[data-testid="review"]').element as HTMLButtonElement).disabled).toBe(true);
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
    const w = mount(ClaimCard, { props: { facts: card.facts, missing: [], citations: card.citations, risk: card.risk, card, status: "awaiting_review", busy: false } });
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
