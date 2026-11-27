import { describe, expect, it } from "vitest";
import { parseSse } from "../src/api/client";
import { applyReview, beginTurn, initialState, reduce } from "../src/store";

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
  it("updates the displayed risk and citations after a reviewer refresh", () => {
    const s = initialState();
    const refreshed = { ...card, risk: { ...card.risk, band: "low", reasons: ["New evidence"] }, citations: [] };
    applyReview(s, "awaiting_review", refreshed as any);
    expect(s.risk?.band).toBe("low");
    expect(s.risk?.reasons).toEqual(["New evidence"]);
    expect(s.citations).toEqual([]);
  });

  it("keeps server history when applying a claim action", () => {
    const s = initialState();
    const history = [{ id: 1, kind: "submitted" as const, actor: "customer", decision: null, note: null, changes: [], created_at: "2026-11-27T10:00:00Z" }];
    applyReview(s, "awaiting_review", card as any, history);
    expect(s.history).toEqual(history);
  });
  it("clears old guidance when replying to a reviewer request", () => {
    const s = initialState();
    s.status = "information_needed";
    s.card = card as any;
    s.citations = [...card.citations];
    s.risk = { ...card.risk, reasons: [...card.risk.reasons] };
    beginTurn(s, "Here is the requested information");
    expect(s.status).toBe("collecting");
    expect(s.card).toBeNull();
    expect(s.citations).toEqual([]);
    expect(s.risk).toBeNull();
  });
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

it("clears an old score as soon as streamed facts have insufficient risk inputs", () => {
  const s = initialState();
  applyReview(s, "assessed", card as any);
  reduce(s, { type: "risk_availability", data: { status: "insufficient_information", missing: ["witnesses"] } });
  expect(s.risk).toBeNull();
  expect(s.riskStatus).toBe("insufficient_information");
  expect(s.riskMissing).toEqual(["witnesses"]);
  applyReview(s, "assessed", { ...card, risk: null, risk_status: "insufficient_information", risk_missing: ["witnesses"] } as any);
  expect(s.riskStatus).toBe("insufficient_information");
});
