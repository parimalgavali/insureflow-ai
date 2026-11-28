import { mount } from "@vue/test-utils";
import { expect, it } from "vitest";
import DocumentChecklist from "../src/components/DocumentChecklist.vue";
import { setLocale } from "../src/i18n";
const file = { id: "file", filename: "estimate.pdf", content_type: "application/pdf", media_type: "pdf", document_type: "repair_estimate" as const, processing_state: "stored", size_bytes: 100, error: null, is_current: true };
const item = { id: "request", label: "Repair estimate", document_type: "repair_estimate" as const, origin: "reviewer" as const, status: "missing" as const, attachment_ids: [] as string[], confirmed_by: null };

it("links a real saved file without locally confirming its contents", async () => {
  setLocale("en");
  const w = mount(DocumentChecklist, { props: { items: [item], attachments: [{ ...file, document_type: "other_document" }], busy: false, editable: true, reviewer: false, canConfirm: false } });
  expect(w.get('[data-testid="document-state-request"]').text()).toBe("Missing");
  expect(w.find('input[type="checkbox"]').exists()).toBe(false);
  await w.get("select").setValue("file");
  await w.get("form").trigger("submit");
  expect(w.emitted("link")?.[0]).toEqual(["request", "file", true]);
  expect(w.get('[data-testid="document-state-request"]').text()).toBe("Missing");
  await w.setProps({ items: [{ ...item, status: "uploaded", attachment_ids: ["file"] }] });
  expect(w.text()).toContain("Uploaded — awaiting reviewer check");
  expect(w.text()).toContain("estimate.pdf");
  expect(w.text()).not.toContain("Confirm after checking");
  w.unmount();
});

it("lets only a reviewer confirm the exact visible copies", async () => {
  setLocale("en");
  const w = mount(DocumentChecklist, { props: { items: [{ ...item, status: "uploaded", attachment_ids: ["file"] }], attachments: [file], busy: false, editable: false, reviewer: true, canConfirm: true } });
  await w.get("button").trigger("click");
  expect(w.emitted("confirm")?.[0]).toEqual(["request", ["file"], true]);
  expect(w.text()).toContain("awaiting reviewer check");
  await w.setProps({ items: [{ ...item, status: "confirmed", attachment_ids: ["file"], confirmed_by: "adjuster" }] });
  expect(w.text()).toContain("Confirmed by reviewer");
  await w.get("button").trigger("click");
  expect(w.emitted("confirm")?.[1]).toEqual(["request", ["file"], false]);
  w.unmount();
});
