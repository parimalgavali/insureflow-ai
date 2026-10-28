import { describe, expect, it } from "vitest";
import { locale, setLocale, t } from "../src/i18n";

describe("i18n", () => {
  it("switches language and interpolates", () => {
    setLocale("en");
    expect(t("card.sendToAdjuster")).toBe("Send to adjuster");
    expect(t("card.page", { page: 31 })).toBe("page 31");
    setLocale("de");
    expect(t("card.sendToAdjuster")).toBe("An Sachbearbeiter senden");
    expect(t("card.page", { page: 31 })).toBe("Seite 31");
    expect(locale.value).toBe("de");
    setLocale("en");
  });

  it("falls back to the key when missing", () => {
    expect(t("nonexistent.key")).toBe("nonexistent.key");
  });

  it("has the same keys in both languages", async () => {
    const en = (await import("../src/i18n/en.json")).default;
    const de = (await import("../src/i18n/de.json")).default;
    expect(Object.keys(de).sort()).toEqual(Object.keys(en).sort());
  });
});
