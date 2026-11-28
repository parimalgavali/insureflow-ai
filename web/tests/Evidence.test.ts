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


it("shows source-linked suggestions separately and offers explicit PDF reading", async () => {
  setLocale("en");
  const attachment = { id: "pdf", filename: "estimate.pdf", content_type: "application/pdf", media_type: "pdf", document_type: "repair_estimate" as const, processing_state: "stored", size_bytes: 100, error: null };
  const w = mount(AttachmentList, { props: { attachments: [attachment], canExtract: true, busy: true } });
  expect(w.get("button").attributes("disabled")).toBeDefined();
  await w.setProps({ busy: false });
  await w.get("button").trigger("click");
  expect(w.emitted("extract")?.[0]).toEqual(["pdf"]);
  await w.setProps({ attachments: [{ ...attachment, processing_state: "ready", suggestions: [{ id: "s", field: "estimated_amount_eur", value: 1200, page: 2, quote: "<script>EUR 1200</script>", status: "pending", source_document_id: "pdf", source_name: "estimate.pdf" }] }] });
  expect(w.text()).toContain("only change claim facts after you accept");
  expect(w.get('[data-testid="evidence-suggestion"]').text()).toContain("1200");
  expect(w.text()).toContain("estimate.pdf · page 2");
  expect(w.find("script").exists()).toBe(false);
  expect(w.find("button").exists()).toBe(false);
  w.unmount();
});


it("requires a separate replacement confirmation and resets it when saved facts change", async () => {
  setLocale("en");
  const suggestion = { id: "s", field: "estimated_amount_eur" as const, value: 1200, page: 1, quote: "EUR 1200", status: "pending", source_document_id: "pdf", source_name: "estimate.pdf" };
  const w = mount(AttachmentList, { props: { facts: { estimated_amount_eur: 900 } as never, canConfirm: true, attachments: [{ id: "pdf", filename: "estimate.pdf", content_type: "application/pdf", media_type: "pdf", document_type: "repair_estimate", processing_state: "ready", size_bytes: 100, error: null, suggestions: [suggestion] }] } });
  const accept = w.findAll("button").find((button) => button.text() === "Accept suggestion")!;
  expect(w.text()).toContain("Saved value: 900");
  expect(w.text()).toContain("Document suggestion: 1200");
  expect(accept.attributes("disabled")).toBeDefined();
  await w.get('input[type="checkbox"]').setValue(true);
  await accept.trigger("click");
  expect(w.emitted("decide")?.[0]).toEqual(["s", { decision: "accept", expected_current: 900, replace_existing: true }]);
  await w.setProps({ facts: { estimated_amount_eur: 1000 } as never });
  expect(accept.attributes("disabled")).toBeDefined();
  await w.findAll("button").find((button) => button.text() === "Reject suggestion")!.trigger("click");
  expect(w.emitted("decide")?.[1]).toEqual(["s", { decision: "reject", expected_current: 1000, replace_existing: false }]);
  w.unmount();
});
