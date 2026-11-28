import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App.vue";
import ChatColumn from "../src/components/ChatColumn.vue";
import HistoryPage from "../src/components/HistoryPage.vue";
import { createConversation, reviewClaim, sendMessage, submitClaim, correctClaimFacts, refreshClaimAssessment, getConversation } from "../src/api/client";
import { initialState, store } from "../src/store";

vi.mock("../src/api/client", () => ({
  createConversation: vi.fn(),
  submitClaim: vi.fn(),
  reviewClaim: vi.fn(),
  sendMessage: vi.fn(),
  fetchEval: vi.fn(),
  fetchClaimHistory: vi.fn(),
  correctClaimFacts: vi.fn(),
  refreshClaimAssessment: vi.fn(),
  getConversation: vi.fn(),
}));

const card = {
  facts: {}, policy: {}, citations: [], risk: null, status: "awaiting_review", review: null,
};

function mountApp() {
  return mount(App, { global: { stubs: {
    ClaimCard: { emits: ["submit", "review", "customerCorrect", "customerRefresh"], template: '<div><button data-testid="send-claim" @click="$emit(\'submit\')">Submit</button><button data-testid="correct-facts" @click="$emit(\'customerCorrect\', { location: \'Berlin\' })">Correct</button><button data-testid="refresh-facts" @click="$emit(\'customerRefresh\')">Refresh</button></div>' },
    ChatColumn: { emits: ["retry", "send"], template: '<button data-testid="retry-action" @click="$emit(\'retry\')">Retry</button>' },
    EvalPage: true,
    ReviewerQueue: true,
    HistoryPage: true,
  } } });
}

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  vi.resetAllMocks();
  Object.assign(store, initialState());
  vi.mocked(createConversation).mockResolvedValue({
    id: "conversation-1", claim_id: "claim-1", language: "en", status: "assessed",
    messages: [], policy: {}, card,
  } as never);
});

describe("customer submission", () => {
  it("saves customer corrections with ordinary access and reloads canonical messages", async () => {
    const updated = { ...card, facts: { location: "Berlin" }, status: "assessed" };
    vi.mocked(correctClaimFacts).mockResolvedValue({ status: "assessed", card: updated, missing: [], history: [] } as never);
    vi.mocked(getConversation).mockResolvedValue({ id: "conversation-1", claim_id: "claim-1", language: "en", status: "assessed", card: updated, policy: {}, messages: [{ id: "edit", role: "user", content: "Confirmed corrections: Berlin" }], missing: [], history: [] } as never);
    const w = mountApp();
    await flushPromises();
    await w.get('[data-testid="correct-facts"]').trigger("click");
    await flushPromises();
    expect(correctClaimFacts).toHaveBeenCalledWith("claim-1", { location: "Berlin" });
    expect(reviewClaim).not.toHaveBeenCalled();
    expect(store.facts?.location).toBe("Berlin");
    expect(store.messages.at(-1)?.content).toContain("Confirmed corrections");
    w.unmount();
  });

  it("retries a failed customer assessment action instead of sending the old chat text", async () => {
    vi.mocked(refreshClaimAssessment).mockRejectedValueOnce(new Error("Connection lost"))
      .mockResolvedValueOnce({ status: "assessed", card } as never);
    vi.mocked(getConversation).mockResolvedValue({ id: "conversation-1", claim_id: "claim-1", language: "en", status: "assessed", card, policy: {}, messages: [] } as never);
    const w = mountApp();
    await flushPromises();
    store.lastUserText = "Old chat message";
    await w.get('[data-testid="refresh-facts"]').trigger("click");
    await flushPromises();
    await w.get('[data-testid="retry-action"]').trigger("click");
    await flushPromises();
    expect(refreshClaimAssessment).toHaveBeenCalledTimes(2);
    expect(sendMessage).not.toHaveBeenCalled();
    expect(store.error).toBeNull();
    w.unmount();
  });
  it("opens a saved history URL without creating a new conversation", async () => {
    window.history.replaceState(null, "", "/#history/claim-1");
    const w = mountApp();
    await flushPromises();
    expect(createConversation).not.toHaveBeenCalled();
    expect(w.getComponent(HistoryPage).props("claimId")).toBe("claim-1");
    w.unmount();
    window.history.replaceState(null, "", "/");
  });
  it("submits with customer access without recording a review", async () => {
    vi.mocked(submitClaim).mockResolvedValue({ status: "awaiting_review", card } as never);
    const w = mountApp();
    await flushPromises();
    await w.get('[data-testid="send-claim"]').trigger("click");
    await flushPromises();
    expect(submitClaim).toHaveBeenCalledWith("claim-1");
    expect(reviewClaim).not.toHaveBeenCalled();
    expect(store.status).toBe("awaiting_review");
    expect(store.card?.review).toBeNull();
    w.unmount();
  });

  it("retries a failed submission instead of resending a chat message", async () => {
    vi.mocked(submitClaim).mockRejectedValueOnce(new Error("Connection lost"))
      .mockResolvedValueOnce({ status: "awaiting_review", card } as never);
    const w = mountApp();
    await flushPromises();
    store.lastUserText = "The incident happened yesterday";
    await w.get('[data-testid="send-claim"]').trigger("click");
    await flushPromises();
    expect(store.error).toBe("Connection lost");
    expect(store.busy).toBe(false);
    await w.get('[data-testid="retry-action"]').trigger("click");
    await flushPromises();
    expect(submitClaim).toHaveBeenCalledTimes(2);
    expect(sendMessage).not.toHaveBeenCalled();
    expect(store.status).toBe("awaiting_review");
    expect(store.error).toBeNull();
    w.unmount();
  });
});


it("retries the original file and operation without duplicating the optimistic message", async () => {
  const w = mountApp();
  await flushPromises();
  store.status = "collecting";
  const file = new File(["sample"], "claim.pdf", { type: "application/pdf" });
  vi.mocked(sendMessage).mockRejectedValueOnce(new Error("Network lost"));
  w.findComponent(ChatColumn).vm.$emit("send", "Original text", file);
  await flushPromises();
  expect(store.busy).toBe(false);
  expect(store.error).toContain("Retry");
  const first = vi.mocked(sendMessage).mock.calls[0];
  expect(first[2]).toBe(file);
  vi.mocked(sendMessage).mockResolvedValueOnce(undefined);
  vi.mocked(getConversation).mockResolvedValueOnce({ id: "conversation-1", claim_id: "claim-1", language: "en", status: "collecting", card: null, policy: {}, messages: [{ id: "saved", role: "user", content: "Original text" }] } as never);
  await w.get('[data-testid="retry-action"]').trigger("click");
  await flushPromises();
  const second = vi.mocked(sendMessage).mock.calls[1];
  expect(second[1]).toBe(first[1]);
  expect(second[2]).toBe(file);
  expect(second[5]).toBe(first[5]);
  expect(first[5]).toBeTruthy();
  expect(store.messages.filter((m) => m.role === "user")).toHaveLength(1);
  expect(store.busy).toBe(false);
  expect(store.error).toBeNull();
  w.unmount();
});
