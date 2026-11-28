import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ClaimHistory from "../src/components/ClaimHistory.vue";
import HistoryPage from "../src/components/HistoryPage.vue";
import { fetchClaimHistory, type HistoryEntry } from "../src/api/client";
import { setLocale } from "../src/i18n";

vi.mock("../src/api/client", () => ({ fetchClaimHistory: vi.fn() }));

const events: HistoryEntry[] = [
  { id: 1, kind: "submitted", actor: "customer", decision: null, note: null, changes: [], created_at: "2026-11-27T10:00:00Z" },
  { id: 2, kind: "corrected", actor: "adjuster", decision: "edit", note: "<b>Witness confirmed</b>", changes: [{ field: "witnesses", before: false, after: true }], created_at: "2026-11-27T10:05:00Z" },
  { id: 3, kind: "review_completed", actor: "adjuster", decision: "accept", note: null, changes: [], created_at: "2026-11-27T10:10:00Z" },
];

beforeEach(() => {
  vi.resetAllMocks();
  setLocale("en");
});

describe("claim history", () => {
  it("shows recorded order, role identity, times, changes and plain-text notes", () => {
    const w = mount(ClaimHistory, { props: { entries: events } });
    expect(w.findAll('[data-testid="history-event"]').map((r) => r.attributes("data-history-kind"))).toEqual(["submitted", "corrected", "review_completed"]);
    expect(w.findAll("time").map((r) => r.attributes("datetime"))).toEqual(events.map((e) => e.created_at));
    expect(w.text()).toContain("Reviewer (shared demo access)");
    expect(w.text()).toContain("Customer (demo access)");
    expect(w.text()).toContain("Witnesses: no → yes");
    expect(w.text()).toContain("<b>Witness confirmed</b>");
    expect(w.find("b").exists()).toBe(false);
    expect(w.text()).toContain("No note provided");
    expect(w.find("input").exists()).toBe(false);
  });

  it("explains that unavailable older activity was not reconstructed", () => {
    const w = mount(ClaimHistory, { props: { entries: [] } });
    expect(w.text()).toContain("No actions have been recorded");
    expect(w.text()).toContain("Earlier activity may not appear");
    expect(w.find('[data-testid="history-event"]').exists()).toBe(false);
  });
});

describe("saved history page", () => {
  it("loads saved data and clears it if a later request fails, then supports retry", async () => {
    vi.mocked(fetchClaimHistory).mockResolvedValueOnce(events)
      .mockRejectedValueOnce(new Error("403 Forbidden"))
      .mockResolvedValueOnce([]);
    const w = mount(HistoryPage, { props: { claimId: "claim-1" } });
    await flushPromises();
    expect(fetchClaimHistory).toHaveBeenCalledWith("claim-1");
    expect(w.findAll('[data-testid="history-event"]')).toHaveLength(3);
    await w.setProps({ claimId: "claim-2" });
    await flushPromises();
    expect(w.get('[role="alert"]').text()).toContain("History could not be loaded");
    expect(w.find('[data-testid="history-event"]').exists()).toBe(false);
    await w.get("form").trigger("submit");
    await flushPromises();
    expect(w.text()).toContain("No actions have been recorded");
    w.unmount();
  });

  it("ignores a late response for a different claim", async () => {
    let finish!: (entries: HistoryEntry[]) => void;
    vi.mocked(fetchClaimHistory).mockReturnValueOnce(new Promise((resolve) => { finish = resolve; }))
      .mockResolvedValueOnce([]);
    const w = mount(HistoryPage, { props: { claimId: "claim-1" } });
    await w.setProps({ claimId: "claim-2" });
    await flushPromises();
    finish(events);
    await flushPromises();
    expect(w.text()).toContain("claim-2");
    expect(w.find('[data-testid="history-event"]').exists()).toBe(false);
    w.unmount();
  });

  it("allows required access credentials to be re-entered without storing them", async () => {
    vi.mocked(fetchClaimHistory).mockRejectedValueOnce(new Error("401 Unauthorized"))
      .mockResolvedValueOnce(events);
    const w = mount(HistoryPage, { props: { claimId: "claim-1" } });
    await flushPromises();
    expect(w.get("label").text()).toBe("Access token (if required)");
    await w.get('input[type="password"]').setValue("reviewer-secret");
    await w.get("form").trigger("submit");
    await flushPromises();
    expect(fetchClaimHistory).toHaveBeenLastCalledWith("claim-1", "reviewer-secret");
    expect(w.findAll('[data-testid="history-event"]')).toHaveLength(3);
    expect(localStorage.getItem("claimpilot_token")).toBeNull();
    expect(sessionStorage.length).toBe(0);
    w.unmount();
  });
});
