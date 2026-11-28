/** Typed client for the ClaimPilot API (mirrors api/agent/schemas.py and the SSE event names). */

export type Language = "de" | "en";
export type CoverageStatus = "likely_covered" | "likely_not_covered" | "unclear" | "no_evidence";
export type ClaimStatus = "collecting" | "assessed" | "awaiting_review" | "information_needed" | "reviewed";

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

export type CoverageSource = "standard_demo" | "uploaded_policy";

export interface Citation {
  source?: CoverageSource;
  document_id?: string | null;
  source_name?: string | null;
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

export type RiskStatus = "pending" | "available" | "insufficient_information" | "unavailable";

export interface RiskSignal {
  score: number;
  band: "low" | "medium" | "high";
  reasons: string[];
  model_version: string;
}

export interface ReviewDecision {
  decision: "accept" | "edit" | "request_info" | "reassess";
  facts_patch?: Record<string, unknown>;
  note?: string | null;
  reviewer?: string;
}

export interface ClaimCard {
  facts: ClaimFacts;
  policy: PolicyContext;
  coverage_status: CoverageStatus;
  coverage_summary: string;
  coverage_source?: CoverageSource;
  coverage_policy_id?: string | null;
  coverage_policy_name?: string | null;
  coverage_policy_ready?: boolean | null;
  coverage_uncertainty?: "missing_facts" | "missing_policy_wording" | "conflicting_evidence" | "human_review" | null;
  citations: Citation[];
  risk: RiskSignal | null;
  risk_status?: RiskStatus;
  risk_missing?: string[];
  cost: CostContext | null;
  missing_documents: string[];
  next_steps: string[];
  status: ClaimStatus;
  review: ReviewDecision | null;
  assessment_stale?: boolean;
  assessment_error?: string | null;
  corrections?: { field: string; before: string | number | boolean | null; after: string | number | boolean | null }[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export type DocumentType = "damage_photo" | "repair_estimate" | "police_report" | "other_document";
export interface EvidenceSuggestion {
  id: string;
  field: keyof ClaimFacts;
  value: string | number | boolean;
  page: number;
  quote: string;
  status: string;
  source_document_id: string;
  source_name: string;
}
export interface EvidenceAttachment {
  id: string;
  filename: string;
  content_type: string;
  media_type: string;
  document_type: DocumentType | "unknown";
  processing_state: string;
  page_count?: number | null;
  suggestions?: EvidenceSuggestion[];
  size_bytes: number;
  error: string | null;
}

export interface Conversation {
  pending_operation_id?: string | null;
  id: string;
  language: Language;
  status: ClaimStatus;
  policy: PolicyContext;
  messages: Message[];
  claim_id: string | null;
  card: ClaimCard | null;
  attachments?: EvidenceAttachment[];
  history?: HistoryEntry[];
  missing?: string[];
}

export interface HistoryEntry {
  id: number;
  kind: "submitted" | "information_requested" | "corrected" | "assessment_refreshed" | "assessment_refresh_failed" | "review_completed";
  actor: string;
  decision: string | null;
  note: string | null;
  changes: { field: string; before: string | number | boolean | null; after: string | number | boolean | null }[];
  created_at: string;
}

export interface ClaimActionResult {
  status: ClaimStatus;
  card: ClaimCard;
  attachments?: EvidenceAttachment[];
  history?: HistoryEntry[];
  missing?: string[];
}

export type AgentEvent =
  | { type: "facts"; data: { facts: ClaimFacts; language: Language } }
  | { type: "missing"; data: { missing: string[] } }
  | { type: "token"; data: { text: string } }
  | { type: "question"; data: { text: string } }
  | { type: "citations"; data: { citations: Citation[] } }
  | { type: "risk_availability"; data: { status: RiskStatus; missing: string[] } }
  | { type: "risk"; data: { risk: RiskSignal | null } }
  | { type: "card"; data: { card: ClaimCard } }
  | { type: "done"; data: { status: ClaimStatus; claim_id: string; awaiting_review: boolean } }
  | { type: "error"; data: { message: string } };

const BASE = import.meta.env.VITE_API_BASE ?? "";

export interface ReviewerClaim {
  id: string;
  conversation_id: string;
  status: ClaimStatus;
  card: ClaimCard | null;
  submitted_at: string | null;
  attachments?: EvidenceAttachment[];
  history?: HistoryEntry[];
  missing?: string[];
}

export interface QueueItem {
  id: string;
  submitted_at: string | null;
  event_type: string;
  location: string | null;
}

export interface ReviewQueue {
  items: QueueItem[];
  has_more: boolean;
}

export async function fetchReviewQueue(token: string, offset = 0): Promise<ReviewQueue> {
  const res = await fetch(`${BASE}/api/claims/review-queue?offset=${offset}`, {
    headers: { authorization: `Bearer ${token}` },
  });
  return (await expectOk(res)).json();
}

export async function fetchReviewerClaim(claimId: string, token: string): Promise<ReviewerClaim> {
  const res = await fetch(`${BASE}/api/claims/review-queue/${claimId}`, {
    headers: { authorization: `Bearer ${token}` },
  });
  return (await expectOk(res)).json();
}

let accessToken: string | null = null;
export function setAccessToken(token: string): void { accessToken = token.trim() || null; }
// Discard credentials left by older versions instead of reusing browser storage.
try { localStorage.removeItem("claimpilot_token"); } catch { /* Storage may be unavailable. */ }

function headers(json = true): HeadersInit {
  const h: Record<string, string> = {};
  if (json) h["content-type"] = "application/json";
  if (accessToken) h.authorization = `Bearer ${accessToken}`;
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
  return (await expectOk(await fetch(`${BASE}/api/conversations/${encodeURIComponent(id)}`, { headers: headers(false) }))).json();
}

export async function fetchClaimHistory(claimId: string, token?: string): Promise<HistoryEntry[]> {
  const res = await fetch(`${BASE}/api/claims/${encodeURIComponent(claimId)}/history`, {
    headers: token ? { authorization: `Bearer ${token}` } : headers(false),
  });
  return (await expectOk(res)).json();
}

/** Submit using customer access; this never records an adjuster decision. */
export async function submitClaim(claimId: string): Promise<ClaimActionResult> {
  const res = await fetch(`${BASE}/api/claims/${claimId}/submit`, { method: "POST", headers: headers() });
  return (await expectOk(res)).json();
}

export async function correctClaimFacts(claimId: string, factsPatch: Record<string, unknown>): Promise<ClaimActionResult> {
  const res = await fetch(`${BASE}/api/claims/${claimId}/facts`, { method: "PATCH", headers: headers(), body: JSON.stringify({ facts_patch: factsPatch }) });
  return (await expectOk(res)).json();
}

export async function refreshClaimAssessment(claimId: string): Promise<ClaimActionResult> {
  const res = await fetch(`${BASE}/api/claims/${claimId}/facts/refresh`, { method: "POST", headers: headers() });
  return (await expectOk(res)).json();
}

/** Review needs the adjuster credential (ADJUSTER_API_TOKEN), asked for each time and never stored. */
export async function reviewClaim(
  claimId: string,
  decision: ReviewDecision,
  askToken: () => string | null = () => null,
): Promise<ClaimActionResult> {
  const token = askToken();
  const h: Record<string, string> = { "content-type": "application/json" };
  if (token) h.authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE}/api/claims/${claimId}/review`, { method: "POST", headers: h, body: JSON.stringify(decision) });
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
  operationId?: string,
  documentType?: DocumentType,
): Promise<void> {
  const form = new FormData();
  form.append("text", text);
  if (operationId) form.append("operation_id", operationId);
  if (file) {
    form.append("file", file);
    if (documentType) form.append("document_type", documentType);
  }
  if (language) form.append("language", language);
  const res = await expectOk(
    await fetch(`${BASE}/api/conversations/${conversationId}/messages`, { method: "POST", headers: headers(false), body: form }),
  );
  return receiveEvents(res, onEvent);
}

export async function retrySavedMessage(conversationId: string, operationId: string, onEvent: (event: AgentEvent) => void): Promise<void> {
  const res = await expectOk(await fetch(`${BASE}/api/conversations/${encodeURIComponent(conversationId)}/messages/${encodeURIComponent(operationId)}/retry`, { method: "POST", headers: headers(false) }));
  return receiveEvents(res, onEvent);
}

async function receiveEvents(res: Response, onEvent: (event: AgentEvent) => void): Promise<void> {
  if (!res.body) throw new Error("streaming not supported by this browser");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let terminal = false;
  const dispatch = (event: AgentEvent) => {
    if (event.type === "done" || event.type === "error") terminal = true;
    onEvent(event);
  };
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseSse(buffer);
    buffer = parsed.rest;
    parsed.events.forEach(dispatch);
  }
  const tail = parseSse(buffer + "\n\n");
  tail.events.forEach(dispatch);
  if (!terminal) throw new Error("Response interrupted. Please retry.");
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


export interface PolicySelection {
  coverage_source: CoverageSource;
  document: { id: string; revision?: number; filename: string; size_bytes: number; status: string; error: string | null; page_count?: number | null; passage_count?: number } | null;
  max_upload_bytes: number;
}
export async function fetchPolicy(conversationId: string): Promise<PolicySelection> {
  return (await expectOk(await fetch(`${BASE}/api/conversations/${encodeURIComponent(conversationId)}/policy`, { headers: headers(false) }))).json();
}
export async function uploadPolicy(conversationId: string, file: File): Promise<PolicySelection> {
  const body = new FormData();
  body.append("file", file);
  return (await expectOk(await fetch(`${BASE}/api/conversations/${encodeURIComponent(conversationId)}/policy`, { method: "POST", headers: headers(false), body }))).json();
}

export async function preparePolicy(conversationId: string): Promise<PolicySelection> {
  return (await expectOk(await fetch(`${BASE}/api/conversations/${encodeURIComponent(conversationId)}/policy/prepare`, { method: "POST", headers: headers(false) }))).json();
}

export async function replacePolicy(conversationId: string, replacesDocumentId: string, file: File): Promise<PolicySelection> {
  const body = new FormData();
  body.append("file", file);
  body.append("replaces_document_id", replacesDocumentId);
  return (await expectOk(await fetch(`${BASE}/api/conversations/${encodeURIComponent(conversationId)}/policy`, { method: "PUT", headers: headers(false), body }))).json();
}


export async function extractEvidence(conversationId: string, attachmentId: string): Promise<EvidenceAttachment> {
  return (await expectOk(await fetch(`${BASE}/api/conversations/${encodeURIComponent(conversationId)}/attachments/${encodeURIComponent(attachmentId)}/extract`, { method: "POST", headers: headers(false) }))).json();
}
