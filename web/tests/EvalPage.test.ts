import { mount, flushPromises } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

vi.mock("../src/api/client", () => ({
  fetchEval: vi.fn(async () => ({
    k: 5,
    threshold: 0.8,
    passed: true,
    summary: { top1: 0.61, top3: 0.89, mrr: 0.75, de_top3: 0.89, en_top3: 0.9 },
    results: [
      { id: "de01", lang: "de", question: "Unfallflucht?", expected: ["A.2.2.2.2"], topic: "x", retrieved: ["A.2.2.2.2", "E.1.1.3"], rank: 1, hit: true },
      { id: "en10", lang: "en", question: "Deductible?", expected: ["A.2.5.8"], topic: "x", retrieved: ["A.2.2.1.4"], rank: null, hit: false },
    ],
  })),
}));

import EvalPage from "../src/components/EvalPage.vue";

describe("EvalPage", () => {
  it("renders the summary and marks hits and misses", async () => {
    const w = mount(EvalPage);
    await flushPromises();
    expect(w.get('[data-testid="eval-summary"]').text()).toMatch(/top-3 89%/);
    expect(w.get('[data-testid="eval-summary"]').text()).toMatch(/pass/);
    expect(w.get('[data-testid="eval-de01"]').classes()).toContain("hit");
    expect(w.get('[data-testid="eval-en10"]').classes()).toContain("miss");
    expect(w.get('[data-testid="eval-en10"]').text()).toMatch(/miss/);
  });
});
