import { expect, it } from "vitest";
import { evidenceReadProblem, evidenceReplacementProblem, pdfProblem } from "../src/evidenceMessages";
import { setLocale } from "../src/i18n";

it("explains empty, scanned, damaged and protected PDFs without promising OCR", () => {
  setLocale("en");
  expect(evidenceReadProblem("empty_pdf")).toContain("empty");
  expect(evidenceReadProblem("no_selectable_text")).toContain("scans are not read automatically");
  expect(evidenceReadProblem("unreadable_pages")).toContain("No document suggestions were saved");
  expect(evidenceReadProblem("damaged_pdf")).toContain("damaged");
  expect(evidenceReplacementProblem(new Error('422 Unprocessable: {"detail":"encrypted_pdf"}'))).toContain("password-protected");
  expect(pdfProblem("invented_code")).toBeNull();
  setLocale("de");
  expect(evidenceReadProblem("encrypted_pdf")).toContain("passwortgeschützt");
  setLocale("en");
});
