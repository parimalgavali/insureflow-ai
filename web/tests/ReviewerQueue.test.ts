import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ReviewerQueue from "../src/components/ReviewerQueue.vue";
import ClaimCard from "../src/components/ClaimCard.vue";
import { fetchReviewQueue, fetchReviewerClaim, confirmChecklistDocument, reviewClaim, type ReviewerClaim } from "../src/api/client";
import { setLocale } from "../src/i18n";

vi.mock("../src/api/client", () => ({
  fetchReviewQueue: vi.fn(), fetchReviewerClaim: vi.fn(), confirmChecklistDocument: vi.fn(), reviewClaim: vi.fn(),
}));

const item = { id: "claim-1", submitted_at: "2026-11-26T12:30:00Z", event_type: "theft", location: "Berlin" };
const detail: ReviewerClaim = {
  id: item.id, conversation_id: "conversation-1", submitted_at: item.submitted_at,
  status: "awaiting_review", card: {
    facts: { incident_date: "2026-11-25", incident_time: null, location: "Berlin", event_type: "theft", description: "Car stolen", third_party_involved: false, third_party_known: false, injuries: false, police_report_filed: true, witnesses: null, damage_description: "Missing vehicle", estimated_amount_eur: null, vehicle_drivable: false, photos_attached: false },
    policy: { product: "teilkasko", deductible_eur: 300 },
    coverage_status: "likely_covered", coverage_summary: "Theft wording [A.2.2.1.2]",
    citations: [{ clause_id: "A.2.2.1.2", title: "Theft", excerpt: "Policy wording", page: 10, score: 0.8 }],
    risk: { band: "medium", score: 0.3, reasons: ["Example reason"], model_version: "test" },
    cost: null, missing_documents: [], next_steps: [], status: "awaiting_review", review: null,
  },
};

beforeEach(() => {
  vi.resetAllMocks();
  setLocale("en");
  vi.mocked(fetchReviewQueue).mockResolvedValue({ items: [item], has_more: false });
  vi.mocked(fetchReviewerClaim).mockResolvedValue(detail);
});

function mountQueue() {
  return mount(ReviewerQueue, { global: { stubs: { ClaimCard: true } } });
}

async function unlock(w: ReturnType<typeof mountQueue>) {
  await w.get('input[type="password"]').setValue("reviewer-secret");
  await w.get("form").trigger("submit");
  await flushPromises();
}

describe("reviewer queue", () => {
  it("requires a credential and clears data after a rejected request", async () => {
    vi.mocked(fetchReviewQueue).mockRejectedValueOnce(new Error("403 Forbidden"));
    const w = mountQueue();
    expect(fetchReviewQueue).not.toHaveBeenCalled();
    await unlock(w);
    expect(w.get('[role="alert"]').text()).toContain("403");
    expect((w.get("input").element as HTMLInputElement).value).toBe("");
    expect(w.findComponent(ClaimCard).exists()).toBe(false);
    await unlock(w);
    expect(w.find('[data-testid="review-claim-claim-1"]').exists()).toBe(true);
    w.unmount();
  });

  it("shows submission dates, opens full claim evidence, and records a review", async () => {
    const w = mountQueue();
    await unlock(w);
    expect(fetchReviewQueue).toHaveBeenCalledWith("reviewer-secret", 0);
    const row = w.get('[data-testid="review-claim-claim-1"]');
    expect(row.text()).toContain("Submitted:");
    expect(row.text()).toContain("Berlin");
    expect(w.find("input").exists()).toBe(false);
    await row.trigger("click");
    await flushPromises();
    const card = w.getComponent(ClaimCard);
    expect(fetchReviewerClaim).toHaveBeenCalledWith("claim-1", "reviewer-secret");
    expect(card.props("facts")!.location).toBe("Berlin");
    expect(card.props("citations")[0].clause_id).toBe("A.2.2.1.2");
    expect(card.props("risk")!.reasons).toEqual(["Example reason"]);
    expect(card.props("reviewer")).toBe(true);
    vi.mocked(reviewClaim).mockResolvedValue({ status: "reviewed", card: { ...detail.card!, status: "reviewed" } });
    vi.mocked(fetchReviewQueue).mockResolvedValue({ items: [], has_more: false });
    card.vm.$emit("review", {});
    await flushPromises();
    expect(w.getComponent(ClaimCard).props("status")).toBe("reviewed");
    expect(w.emitted("reviewed")?.[0]?.[0]).toMatchObject({ id: "claim-1", status: "reviewed" });
    expect(w.text()).toContain("No claims are waiting");
    expect(localStorage.getItem("claimpilot_token")).toBeNull();
    expect(sessionStorage.length).toBe(0);
    w.unmount();
  });

  it("does not reveal a late response after the queue is locked", async () => {
    let resolveDetail!: (value: ReviewerClaim) => void;
    vi.mocked(fetchReviewerClaim).mockReturnValue(new Promise((resolve) => { resolveDetail = resolve; }));
    const w = mountQueue();
    await unlock(w);
    await w.get('[data-testid="review-claim-claim-1"]').trigger("click");
    await w.findAll("button").find((b) => b.text() === "Lock queue")!.trigger("click");
    resolveDetail(detail);
    await flushPromises();
    expect(w.findComponent(ClaimCard).exists()).toBe(false);
    expect(w.find('[data-testid="review-claim-claim-1"]').exists()).toBe(false);
    expect(w.find('input[type="password"]').exists()).toBe(true);
    w.unmount();
  });

  it("sends an information request without accepting the claim", async () => {
    const w = mountQueue();
    await unlock(w);
    await w.get('[data-testid="review-claim-claim-1"]').trigger("click");
    await flushPromises();
    vi.mocked(reviewClaim).mockResolvedValue({ status: "information_needed", card: { ...detail.card!, status: "information_needed", review: { decision: "request_info", note: "Police report please" } } });
    vi.mocked(fetchReviewQueue).mockResolvedValue({ items: [], has_more: false });
    w.getComponent(ClaimCard).vm.$emit("requestInfo", "Police report please");
    await flushPromises();
    expect(reviewClaim).toHaveBeenCalledWith("claim-1", { decision: "request_info", note: "Police report please" }, expect.any(Function));
    expect(w.getComponent(ClaimCard).props("status")).toBe("information_needed");
    expect(w.emitted("reviewed")?.[0]?.[0]).toMatchObject({ status: "information_needed" });
    expect(w.find('[data-testid="review-claim-claim-1"]').exists()).toBe(false);
    w.unmount();
  });

  it("loads more claims and labels missing historical dates honestly", async () => {
    vi.mocked(fetchReviewQueue).mockResolvedValueOnce({ items: [item], has_more: true })
      .mockResolvedValueOnce({ items: [{ ...item, id: "claim-2", submitted_at: null }], has_more: false });
    const w = mountQueue();
    await unlock(w);
    await w.findAll("button").find((b) => b.text() === "Load more")!.trigger("click");
    await flushPromises();
    expect(fetchReviewQueue).toHaveBeenLastCalledWith("reviewer-secret", 1);
    expect(w.get('[data-testid="review-claim-claim-2"]').text()).toContain("Date unavailable");
    expect(w.find('[data-testid="review-claim-claim-1"]').exists()).toBe(true);
    w.unmount();
  });

  it("keeps the selected claim and credential when a correction needs fixing", async () => {
    const w = mountQueue();
    await unlock(w);
    await w.get('[data-testid="review-claim-claim-1"]').trigger("click");
    await flushPromises();
    vi.mocked(reviewClaim).mockRejectedValue(new Error("422 Unprocessable Entity"));
    w.getComponent(ClaimCard).vm.$emit("review", { witnesses: "maybe" });
    await flushPromises();
    expect(w.get('[role="alert"]').text()).toContain("correction is not valid");
    expect(w.findComponent(ClaimCard).exists()).toBe(true);
    expect(w.find('input[type="password"]').exists()).toBe(false);
    expect(w.getComponent(ClaimCard).props("busy")).toBe(false);
    w.unmount();
  });

  it("keeps corrections pending and retries a failed assessment without accepting the claim", async () => {
    const w = mountQueue();
    await unlock(w);
    await w.get('[data-testid="review-claim-claim-1"]').trigger("click");
    await flushPromises();
    vi.mocked(reviewClaim).mockResolvedValueOnce({ status: "awaiting_review", card: { ...detail.card!, assessment_stale: true, assessment_error: "Refresh failed" } })
      .mockResolvedValueOnce({ status: "awaiting_review", card: { ...detail.card!, assessment_stale: false, risk: { ...detail.card!.risk!, band: "low", reasons: ["Updated reason"] } } });
    w.getComponent(ClaimCard).vm.$emit("review", { police_report_filed: false });
    await flushPromises();
    expect(w.getComponent(ClaimCard).props("card")?.assessment_stale).toBe(true);
    w.getComponent(ClaimCard).vm.$emit("reassess");
    await flushPromises();
    expect(reviewClaim).toHaveBeenLastCalledWith("claim-1", { decision: "reassess" }, expect.any(Function));
    expect(w.getComponent(ClaimCard).props("card")?.assessment_stale).toBe(false);
    expect(w.getComponent(ClaimCard).props("risk")?.reasons).toEqual(["Updated reason"]);
    expect(w.getComponent(ClaimCard).props("status")).toBe("awaiting_review");
    w.unmount();
  });
});


it("confirms document copies using the reviewer credential and keeps the claim pending", async () => {
  const w = mountQueue();
  await unlock(w);
  await w.get('[data-testid="review-claim-claim-1"]').trigger("click");
  await flushPromises();
  vi.mocked(confirmChecklistDocument).mockResolvedValue({ status: "awaiting_review", card: detail.card, document_checklist: [{ id: "request", label: "Estimate", document_type: "repair_estimate", origin: "assessment", status: "confirmed", attachment_ids: ["file"], confirmed_by: "adjuster" }] } as never);
  w.getComponent(ClaimCard).vm.$emit("confirmDocument", "request", ["file"], true);
  await flushPromises();
  expect(confirmChecklistDocument).toHaveBeenCalledWith("claim-1", "request", ["file"], true, "reviewer-secret");
  expect(w.getComponent(ClaimCard).props("status")).toBe("awaiting_review");
  expect(w.getComponent(ClaimCard).props("checklist")?.[0].status).toBe("confirmed");
  expect(reviewClaim).not.toHaveBeenCalled();
  w.unmount();
});
