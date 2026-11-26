import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App.vue";
import { createConversation, reviewClaim, sendMessage, submitClaim } from "../src/api/client";
import { initialState, store } from "../src/store";

vi.mock("../src/api/client", () => ({
  createConversation: vi.fn(),
  submitClaim: vi.fn(),
  reviewClaim: vi.fn(),
  sendMessage: vi.fn(),
  fetchEval: vi.fn(),
}));

const card = {
  facts: {}, policy: {}, citations: [], risk: null, status: "awaiting_review", review: null,
};

function mountApp() {
  return mount(App, { global: { stubs: {
    ClaimCard: { emits: ["submit", "review"], template: '<button data-testid="send-claim" @click="$emit(\'submit\')">Submit</button>' },
    ChatColumn: { emits: ["retry"], template: '<button data-testid="retry-action" @click="$emit(\'retry\')">Retry</button>' },
    EvalPage: true,
    ReviewerQueue: true,
  } } });
}

beforeEach(() => {
  vi.resetAllMocks();
  Object.assign(store, initialState());
  vi.mocked(createConversation).mockResolvedValue({
    id: "conversation-1", claim_id: "claim-1", language: "en", status: "assessed",
    messages: [], policy: {}, card,
  } as never);
});

describe("customer submission", () => {
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
