import { t } from "./i18n";

const PDF_ERRORS: Record<string, string> = {
  empty_file: "evidence.emptyFile", empty_pdf: "evidence.emptyPdf", no_readable_text: "evidence.emptyPdf",
  no_selectable_text: "evidence.scannedPdf", unreadable_page: "evidence.scannedPdf",
  unreadable_pages: "evidence.partialPdf", unreadable_pdf: "evidence.damagedPdf", damaged_pdf: "evidence.damagedPdf",
  encrypted_pdf: "evidence.protectedPdf", same_copy: "evidence.sameCopy",
};
export function evidenceErrorCode(error: unknown): string | null {
  return error instanceof Error ? /"detail"\s*:\s*"([a-z_]+)"/.exec(error.message)?.[1] ?? null : null;
}
export function pdfProblem(code: string | null): string | null {
  return code && PDF_ERRORS[code] ? t(PDF_ERRORS[code]) : null;
}
export function evidenceReadProblem(code: string | null): string {
  return pdfProblem(code) ?? t(code === "document_text_too_long" ? "evidence.readTooLong" : "evidence.readFailed");
}
export function evidenceReplacementProblem(error: unknown): string {
  const known = pdfProblem(evidenceErrorCode(error));
  if (known) return known;
  const message = error instanceof Error ? error.message : "";
  return t(message.startsWith("413 ") ? "evidence.copyTooLarge" : message.startsWith("415 ") ? "evidence.copyPdfRequired" : message.startsWith("422 ") ? "evidence.copyInvalid" : message.startsWith("409 ") ? "evidence.copyConflict" : "evidence.replaceFailed");
}
