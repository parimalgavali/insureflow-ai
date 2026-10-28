import { describe, expect, it } from "vitest";
import { parseSse } from "../src/api/client";
import { beginTurn, initialState, reduce } from "../src/store";

const card = {
  facts: { event_type: "hit_and_run", incident_date: "2026-10-25", photos_attached: false } as any,
  policy: { product: "vollkasko", deductible_eur: 300 },
  coverage_status: "likely_covered",
  coverage_summary: "Covered [A.2.2.2.2].",
  citations: [{ clause_id: "A.2.2.2.2", title: "Unfall", excerpt: "…", page: 11, score: 0.8 }],
  risk: { score: 0.4, band: "medium", reasons: ["a", "b", "c"], model_version: "x" },
  missing_documents: ["Photos"],
  next_steps: ["Review"],
  status: "awaiting_review",
  review: null,
} as const;

describe("parseSse", () => {
  it("splits complete blocks and keeps the remainder", () => {
    const { events, rest } = parseSse('event: token\ndata: {"text":"Hal"}\n\nevent: token\ndata: {"text":"lo"}\n\nevent: done\ndata: {"sta');
    expect(events.map((e) => e.type)).toEqual(["token", "token"]);
    expect(rest).toBe('event: done\ndata: {"sta');
  });
});

describe("reduce", () => {
  it("streams tokens into the pending assistant bubble and finishes on done", () => {
    const s = initialState();
    beginTurn(s, "hi");
    expect(s.busy).toBe(true);
    reduce(s, { type: "facts", data: { facts: card.facts, language: "de" } });
    reduce(s, { type: "missing", data: { missing: ["incident_date"] } });
    reduce(s, { type: "token", data: { text: "Wann " } });
    reduce(s, { type: "token", data: { text: "genau?" } });
    reduce(s, { type: "question", data: { text: "Wann genau?" } });
    reduce(s, { type: "done", data: { status: "collecting", claim_id: "c1", awaiting_review: false } });
    expect(s.messages.at(-1)).toMatchObject({ role: "assistant", content: "Wann genau?", streaming: false });
    expect(s.missing).toEqual(["incident_date"]);
    expect(s.busy).toBe(false);
    expect(s.claimId).toBe("c1");
  });

  it("fills the card from citations/risk/card events", () => {
    const s = initialState();
    beginTurn(s, "more");
    reduce(s, { type: "citations", data: { citations: card.citations as any } });
    reduce(s, { type: "risk", data: { risk: card.risk as any } });
    reduce(s, { type: "card", data: { card: card as any } });
    reduce(s, { type: "done", data: { status: "awaiting_review", claim_id: "c1", awaiting_review: true } });
    expect(s.status).toBe("awaiting_review");
    expect(s.card?.coverage_status).toBe("likely_covered");
    expect(s.risk?.band).toBe("medium");
    expect(s.messages.at(-1)?.content).toBe("Covered [A.2.2.2.2].");
  });

  it("drops the empty bubble and records the error", () => {
    const s = initialState();
    beginTurn(s, "x");
    reduce(s, { type: "error", data: { message: "boom" } });
    expect(s.error).toBe("boom");
    expect(s.messages.map((m) => m.role)).toEqual(["user"]);
  });
});
