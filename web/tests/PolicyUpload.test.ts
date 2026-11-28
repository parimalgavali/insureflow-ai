import { mount, flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PolicyUpload from "../src/components/PolicyUpload.vue";
import { fetchPolicy, uploadPolicy } from "../src/api/client";
vi.mock("../src/api/client", () => ({ fetchPolicy: vi.fn(), uploadPolicy: vi.fn() }));
const empty = { coverage_source: "standard_demo" as const, document: null, max_upload_bytes: 1024 * 1024 };
const saved = { ...empty, document: { id: "document", filename: "sample.pdf", size_bytes: 12, status: "uploaded", error: null } };
const props = { conversationId: "conversation", busy: false, canUpload: true };
beforeEach(() => { vi.resetAllMocks(); vi.mocked(fetchPolicy).mockResolvedValue(empty); });
async function choose(w: ReturnType<typeof mount>, size = 12) {
  const input = w.get('input[type="file"]');
  const file = new File([new Uint8Array(size)], "sample.pdf", { type: "application/pdf" });
  Object.defineProperty(input.element, "files", { value: [file], configurable: true });
  await input.trigger("change");
  return file;
}
describe("policy upload", () => {
  it("keeps demo wording explicit and labels an uploaded file as awaiting preparation", async () => {
    vi.mocked(uploadPolicy).mockResolvedValue(saved);
    const w = mount(PolicyUpload, { props });
    await flushPromises();
    expect(w.get('[data-testid="policy-source"]').text()).toContain("standard GDV");
    const file = await choose(w);
    await w.get("form").trigger("submit");
    await flushPromises();
    expect(uploadPolicy).toHaveBeenCalledWith("conversation", file);
    expect(w.get('[data-testid="policy-filename"]').text()).toBe("sample.pdf");
    expect(w.get('[data-testid="policy-status"]').text()).toContain("awaiting text preparation");
    expect(w.text()).toContain("answers still use demo wording");
    expect(w.emitted("busy")).toEqual([[true], [false]]);
    w.unmount();
  });
  it("shows errors and allows retry with the selected file", async () => {
    vi.mocked(uploadPolicy).mockRejectedValueOnce(new Error("422 invalid_pdf")).mockResolvedValueOnce(saved);
    const w = mount(PolicyUpload, { props });
    await flushPromises();
    const file = await choose(w);
    await w.get("form").trigger("submit");
    await flushPromises();
    expect(w.get('[role="alert"]').text()).toContain("unencrypted, valid PDF");
    await w.get("form").trigger("submit");
    await flushPromises();
    expect(uploadPolicy).toHaveBeenLastCalledWith("conversation", file);
    expect(w.find('[role="alert"]').exists()).toBe(false);
    w.unmount();
  });
  it("rejects oversized input before upload and respects locked claims", async () => {
    vi.mocked(fetchPolicy).mockResolvedValue({ ...empty, max_upload_bytes: 10 });
    const w = mount(PolicyUpload, { props });
    await flushPromises();
    await choose(w, 11);
    await w.get("form").trigger("submit");
    expect(uploadPolicy).not.toHaveBeenCalled();
    expect(w.get('[role="alert"]').text()).toContain("size limit");
    await w.setProps({ canUpload: false });
    expect(w.find('input[type="file"]').exists()).toBe(false);
    w.unmount();
  });
  it("loads the saved selection without another upload", async () => {
    vi.mocked(fetchPolicy).mockResolvedValue(saved);
    const w = mount(PolicyUpload, { props });
    await flushPromises();
    expect(w.get('[data-testid="policy-filename"]').text()).toBe("sample.pdf");
    expect(uploadPolicy).not.toHaveBeenCalled();
    w.unmount();
  });
});
