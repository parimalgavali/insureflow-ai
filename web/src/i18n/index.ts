import { ref } from "vue";
import type { Language } from "../api/client";
import de from "./de.json";
import en from "./en.json";

const MESSAGES: Record<Language, Record<string, string>> = { en, de };
const STORAGE_KEY = "claimpilot_lang";

function initial(): Language {
  const saved = typeof localStorage !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
  if (saved === "de" || saved === "en") return saved;
  const nav = typeof navigator !== "undefined" ? navigator.language : "en";
  return nav.toLowerCase().startsWith("de") ? "de" : "en";
}

/** UI locale. The conversation language follows it (see store.setLanguage). */
export const locale = ref<Language>(initial());

export function setLocale(lang: Language): void {
  locale.value = lang;
  if (typeof localStorage !== "undefined") localStorage.setItem(STORAGE_KEY, lang);
  if (typeof document !== "undefined") document.documentElement.lang = lang;
}

/** Translate `key`, interpolating `{name}` placeholders; falls back to English, then the key. */
export function t(key: string, vars: Record<string, string | number> = {}): string {
  const text = MESSAGES[locale.value][key] ?? MESSAGES.en[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, name: string) => String(vars[name] ?? `{${name}}`));
}
