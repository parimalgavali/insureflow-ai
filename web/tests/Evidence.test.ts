import { mount } from "@vue/test-utils";
import { expect, it } from "vitest";
import ChatColumn from "../src/components/ChatColumn.vue";
import AttachmentList from "../src/components/AttachmentList.vue";
import { setLocale } from "../src/i18n";

it("labels PDFs as documents and restores a rejected draft for editing", async () => {
  setLocale("en");
  const w = mount(ChatColumn, { props: { messages: [], missing: [], busy: false, error: null, canSend: true } });
  const file = new File(["PDF"], "estimate.pdf", { type: "application/pdf" });
  Object.defineProperty(w.get('input[type="file"]').element, "files", { value: [file], configurable: true });
  await w.get('input[type="file"]').trigger("change");
  expect(w.find('option[value="damage_photo"]').exists()).toBe(false);
  await w.get("select").setValue("repair_estimate");
  await w.get("textarea").setValue("My estimate");
  await w.get("form").trigger("submit");
  expect(w.emitted("send")?.[0]).toEqual(["My estimate", file, "repair_estimate"]);
  expect(w.find("select").exists()).toBe(false);
  await w.setProps({ error: "Choose another file", retryable: false, restoredDraft: { text: "My estimate", file, documentType: "repair_estimate" } });
  expect((w.get("textarea").element as HTMLTextAreaElement).value).toBe("My estimate");
  expect((w.get("select").element as HTMLSelectElement).value).toBe("repair_estimate");
  expect(w.get('[role="alert"]').find("button").exists()).toBe(false);
  await w.get(".attach button").trigger("click");
  expect(w.find("select").exists()).toBe(false);
  w.unmount();
});

it("shows stored attachment labels as plain text and keeps legacy files unverified", () => {
  setLocale("en");
  const w = mount(AttachmentList, { props: { attachments: [
    { id: "a", filename: "<script>report.pdf</script>", content_type: "application/pdf", media_type: "pdf", document_type: "police_report", processing_state: "stored", size_bytes: 1, error: null },
    { id: "b", filename: "legacy.png", content_type: "image/png", media_type: "unknown", document_type: "unknown", processing_state: "unknown", size_bytes: 1, error: null },
  ] } });
  expect(w.text()).toContain("Police report · PDF");
  expect(w.text()).toContain("Not yet analysed");
  expect(w.text()).toContain("Older upload");
  expect(w.text()).toContain("<script>report.pdf</script>");
  expect(w.find("script").exists()).toBe(false);
  w.unmount();
});
