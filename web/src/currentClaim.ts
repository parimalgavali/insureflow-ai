/** Only a conversation identifier is persisted; credentials stay in memory. */
const KEY = "claimpilot_conversation_id";
export function currentClaim(): string | null {
  try { return localStorage.getItem(KEY); } catch { return null; }
}
export function rememberClaim(id: string): void {
  try { localStorage.setItem(KEY, id); } catch { /* The current page remains usable. */ }
}
