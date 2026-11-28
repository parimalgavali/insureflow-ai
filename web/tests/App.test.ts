import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App.vue";
import PolicyUpload from "../src/components/PolicyUpload.vue";
import ChatColumn from "../src/components/ChatColumn.vue";
import HistoryPage from "../src/components/HistoryPage.vue";
import { createConversation, reviewClaim, sendMessage, submitClaim, correctClaimFacts, refreshClaimAssessment, getConversation, setAccessToken, retrySavedMessage } from "../src/api/client";
import { initialState, store } from "../src/store";

vi.mock("../src/api/client", () => ({
  createConversation: vi.fn(),
  setAccessToken: vi.fn(),
  retrySavedMessage: vi.fn(),
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
    ChatColumn: { props: ["canSend"], emits: ["retry", "send"], template: '<button data-testid="retry-action" @click="$emit(\'retry\')">Retry</button>' },
    PolicyUpload: true,
    EvalPage: true,
    ReviewerQueue: true,
    HistoryPage: true,
  } } });
}

beforeEach(() => {
  localStorage.removeItem("claimpilot_conversation_id");
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
  w.findComponent(ChatColumn).vm.$emit("send", "Original text", file, "repair_estimate");
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
  expect(second[6]).toBe("repair_estimate");
  expect(first[5]).toBeTruthy();
  expect(store.messages.filter((m) => m.role === "user")).toHaveLength(1);
  expect(store.busy).toBe(false);
  expect(store.error).toBeNull();
  w.unmount();
});


it.each(["collecting", "assessed", "awaiting_review", "information_needed", "reviewed"])("restores a saved %s claim instead of creating another conversation", async (status) => {
  localStorage.setItem("claimpilot_conversation_id", "saved-conversation");
  vi.mocked(getConversation).mockResolvedValueOnce({ id: "saved-conversation", claim_id: "saved-claim", language: "en", status, card: { ...card, status }, policy: {}, messages: [{ id: "saved", role: "user", content: "Saved message" }] } as never);
  const w = mountApp();
  await flushPromises();
  expect(createConversation).not.toHaveBeenCalled();
  expect(getConversation).toHaveBeenCalledWith("saved-conversation");
  expect(store.status).toBe(status);
  expect(store.messages[0].content).toBe("Saved message");
  expect(w.findComponent(ChatColumn).props("canSend")).toBe(["collecting", "information_needed"].includes(status));
  w.unmount();
});

it("keeps an inaccessible saved claim and accepts an in-memory credential for retry", async () => {
  localStorage.setItem("claimpilot_conversation_id", "saved-conversation");
  vi.mocked(getConversation).mockRejectedValueOnce(new Error("401 Unauthorized"))
    .mockResolvedValueOnce({ id: "saved-conversation", claim_id: "claim-1", language: "en", status: "collecting", card: null, policy: {}, messages: [] } as never);
  const w = mountApp();
  await flushPromises();
  expect(w.get('[role="alert"]').text()).toContain("could not open");
  expect(w.findComponent(ChatColumn).exists()).toBe(false);
  expect(createConversation).not.toHaveBeenCalled();
  expect(localStorage.getItem("claimpilot_conversation_id")).toBe("saved-conversation");
  await w.get('#claim-access').setValue("sample-access");
  await w.get('[data-testid="claim-session"] form').trigger("submit");
  await flushPromises();
  expect(setAccessToken).toHaveBeenCalledWith("sample-access");
  expect(localStorage.getItem("claimpilot_token")).toBeNull();
  expect(sessionStorage.getItem("claimpilot_token")).toBeNull();
  expect(w.find('[role="alert"]').exists()).toBe(false);
  w.unmount();
});

it("creates a new claim only after an explicit action and keeps the saved one intact", async () => {
  localStorage.setItem("claimpilot_conversation_id", "old-conversation");
  vi.mocked(getConversation).mockResolvedValueOnce({ id: "old-conversation", claim_id: "old-claim", language: "en", status: "reviewed", card, policy: {}, messages: [] } as never);
  const w = mountApp();
  await flushPromises();
  await w.get('[data-testid="new-claim"]').trigger("click");
  await flushPromises();
  expect(createConversation).toHaveBeenCalledTimes(1);
  expect(store.conversationId).toBe("conversation-1");
  expect(localStorage.getItem("claimpilot_conversation_id")).toBe("conversation-1");
  expect(getConversation).toHaveBeenCalledTimes(1);
  w.unmount();
});

it("restores and retries an unfinished saved message without its old in-memory file", async () => {
  localStorage.setItem("claimpilot_conversation_id", "saved-conversation");
  const conversation = { id: "saved-conversation", claim_id: "claim-1", language: "en", status: "collecting", card: null, policy: {}, messages: [{ id: "saved", role: "user", content: "Original message [Attachment: saved.pdf]" }] };
  vi.mocked(getConversation).mockResolvedValueOnce({ ...conversation, pending_operation_id: "saved-operation" } as never)
    .mockResolvedValueOnce({ ...conversation, pending_operation_id: null } as never);
  vi.mocked(retrySavedMessage).mockResolvedValue(undefined);
  const w = mountApp();
  await flushPromises();
  expect(store.error).toContain("unfinished");
  expect(w.findComponent(ChatColumn).props("canSend")).toBe(false);
  await w.get('[data-testid="retry-action"]').trigger("click");
  await flushPromises();
  expect(retrySavedMessage).toHaveBeenCalledWith("saved-conversation", "saved-operation", expect.any(Function));
  expect(sendMessage).not.toHaveBeenCalled();
  expect(store.pendingOperationId).toBeNull();
  expect(store.error).toBeNull();
  expect(w.findComponent(ChatColumn).props("canSend")).toBe(true);
  w.unmount();
});


it("reloads the canonical assessment after a policy selection change", async () => {
  const w = mountApp();
  await flushPromises();
  vi.mocked(getConversation).mockResolvedValueOnce({ id: "conversation-1", claim_id: "claim-1", language: "en", status: "assessed", card: { ...card, assessment_stale: true }, policy: {}, messages: [] } as never);
  w.findComponent(PolicyUpload).vm.$emit("changed", "conversation-1");
  await flushPromises();
  expect(getConversation).toHaveBeenCalledWith("conversation-1");
  expect(store.card?.assessment_stale).toBe(true);
  expect(store.busy).toBe(false);
  w.unmount();
});


it.each([413, 415, 422])("returns rejected %s uploads to an editable draft with no stuck retry", async (status) => {
  const w = mountApp();
  await flushPromises();
  store.status = "information_needed";
  const previousCard = store.card;
  const file = new File(["bad"], "broken.pdf", { type: "application/pdf" });
  vi.mocked(sendMessage).mockRejectedValueOnce(new Error(`${status} Invalid upload`));
  w.findComponent(ChatColumn).vm.$emit("send", "Keep this message", file, "repair_estimate");
  await flushPromises();
  expect(store.status).toBe("information_needed");
  expect(store.card).toBe(previousCard);
  expect(store.messages).toHaveLength(0);
  expect(w.findComponent(ChatColumn).props("canSend")).toBe(true);
  expect(w.findComponent(ChatColumn).attributes("retryable")).toBe("false");
  expect(store.error).toContain("draft");
  expect(store.busy).toBe(false);
  // The corrected upload starts a new operation; the rejected one was never saved.
  vi.mocked(sendMessage).mockResolvedValueOnce(undefined);
  vi.mocked(getConversation).mockResolvedValueOnce({ id: "conversation-1", claim_id: "claim-1", language: "en", status: "collecting", card: null, policy: {}, messages: [], attachments: [] } as never);
  w.findComponent(ChatColumn).vm.$emit("send", "Keep this message", null, "other_document");
  await flushPromises();
  expect(vi.mocked(sendMessage).mock.calls[1][5]).not.toBe(vi.mocked(sendMessage).mock.calls[0][5]);
  expect(store.error).toBeNull();
  w.unmount();
});
