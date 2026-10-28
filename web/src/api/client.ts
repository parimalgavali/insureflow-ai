/** Typed client for the ClaimPilot API (mirrors api/agent/schemas.py and the SSE event names). */

export type Language = "de" | "en";
export type CoverageStatus = "likely_covered" | "likely_not_covered" | "unclear" | "no_evidence";
export type ClaimStatus = "collecting" | "assessed" | "awaiting_review" | "reviewed";

export interface ClaimFacts {
  incident_date: string | null;
  incident_time: string | null;
  location: string | null;
  event_type: string;
  description: string | null;
  third_party_involved: boolean | null;
  third_party_known: boolean | null;
  injuries: boolean | null;
  police_report_filed: boolean | null;
  witnesses: boolean | null;
  damage_description: string | null;
  estimated_amount_eur: number | null;
  vehicle_drivable: boolean | null;
  photos_attached: boolean;
}

export interface PolicyContext {
  product: "haftpflicht" | "teilkasko" | "vollkasko";
  deductible_eur: number;
}

export interface Citation {
  clause_id: string;
  title: string;
  excerpt: string;
  page: number | null;
  score: number | null;
}

export interface CostContext {
  claims_per_year: number;
  claim_eur: number;
  annual_cost_eur: number;
  portfolio_claim_eur: number;
  basis: string;
}

export interface RiskSignal {
  score: number;
  band: "low" | "medium" | "high";
  reasons: string[];
  model_version: string;
}

export interface ReviewDecision {
  decision: "accept" | "edit" | "request_info";
  facts_patch?: Record<string, unknown>;
  note?: string | null;
}

export interface ClaimCard {
  facts: ClaimFacts;
  policy: PolicyContext;
  coverage_status: CoverageStatus;
  coverage_summary: string;
  citations: Citation[];
  risk: RiskSignal | null;
  cost: CostContext | null;
  missing_documents: string[];
  next_steps: string[];
  status: ClaimStatus;
  review: ReviewDecision | null;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  language: Language;
  status: ClaimStatus;
  policy: PolicyContext;
  messages: Message[];
  claim_id: string | null;
  card: ClaimCard | null;
}

export type AgentEvent =
  | { type: "facts"; data: { facts: ClaimFacts; language: Language } }
  | { type: "missing"; data: { missing: string[] } }
  | { type: "token"; data: { text: string } }
  | { type: "question"; data: { text: string } }
  | { type: "citations"; data: { citations: Citation[] } }
  | { type: "risk"; data: { risk: RiskSignal | null } }
  | { type: "card"; data: { card: ClaimCard } }
  | { type: "done"; data: { status: ClaimStatus; claim_id: string; awaiting_review: boolean } }
  | { type: "error"; data: { message: string } };

const BASE = import.meta.env.VITE_API_BASE ?? "";

function headers(json = true): HeadersInit {
  const h: Record<string, string> = {};
  if (json) h["content-type"] = "application/json";
  const token = typeof localStorage !== "undefined" ? localStorage.getItem("claimpilot_token") : null;
  if (token) h.authorization = `Bearer ${token}`;
  return h;
}

async function expectOk(res: Response): Promise<Response> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${(await res.text()).slice(0, 200)}`);
  return res;
}

export async function createConversation(language: Language, policy?: Partial<PolicyContext>): Promise<Conversation> {
  const res = await fetch(`${BASE}/api/conversations`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ language, policy: { product: "vollkasko", deductible_eur: 300, ...policy } }),
  });
  return (await expectOk(res)).json();
}

export async function getConversation(id: string): Promise<Conversation> {
  return (await expectOk(await fetch(`${BASE}/api/conversations/${id}`, { headers: headers(false) }))).json();
}

export async function reviewClaim(claimId: string, decision: ReviewDecision): Promise<{ status: ClaimStatus; card: ClaimCard }> {
  const res = await fetch(`${BASE}/api/claims/${claimId}/review`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(decision),
  });
  return (await expectOk(res)).json();
}

/** Parse complete SSE blocks out of a buffer; returns events and the unconsumed remainder. */
export function parseSse(buffer: string): { events: AgentEvent[]; rest: string } {
  const events: AgentEvent[] = [];
  let rest = buffer;
  let idx: number;
  while ((idx = rest.indexOf("\n\n")) !== -1) {
    const block = rest.slice(0, idx);
    rest = rest.slice(idx + 2);
    let type = "";
    const dataLines: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) type = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
    }
    if (!type) continue;
    events.push({ type, data: JSON.parse(dataLines.join("\n") || "null") } as AgentEvent);
  }
  return { events, rest };
}

export async function sendMessage(
  conversationId: string,
  text: string,
  file: File | null,
  onEvent: (event: AgentEvent) => void,
  language?: Language,
): Promise<void> {
  const form = new FormData();
  form.append("text", text);
  if (file) form.append("file", file);
  if (language) form.append("language", language);
  const res = await expectOk(
    await fetch(`${BASE}/api/conversations/${conversationId}/messages`, { method: "POST", headers: headers(false), body: form }),
  );
  if (!res.body) throw new Error("streaming not supported by this browser");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseSse(buffer);
    buffer = parsed.rest;
    parsed.events.forEach(onEvent);
  }
  const tail = parseSse(buffer + "\n\n");
  tail.events.forEach(onEvent);
}

export interface EvalRow {
  id: string;
  lang: Language;
  question: string;
  expected: string[];
  topic: string;
  retrieved: string[];
  rank: number | null;
  hit: boolean;
}

export interface EvalReport {
  k: number;
  threshold: number;
  passed: boolean;
  summary: Record<string, number>;
  results: EvalRow[];
}

/** Dev-only: retrieval eval over the hand-written DE/EN questions (404 when EVAL_PAGE is off). */
export async function fetchEval(): Promise<EvalReport> {
  const res = await expectOk(await fetch(`${BASE}/api/eval`, { headers: headers(true) }));
  return (await res.json()) as EvalReport;
}
