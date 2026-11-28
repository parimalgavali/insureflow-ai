/** One reactive store; every SSE event is reduced here so components stay dumb. */
import { reactive } from "vue";
import type { AgentEvent, Citation, ClaimCard, ClaimFacts, ClaimStatus, Conversation, Language, RiskSignal, RiskStatus, HistoryEntry } from "./api/client";

export interface ChatItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

export interface State {
  conversationId: string | null;
  claimId: string | null;
  language: Language;
  messages: ChatItem[];
  facts: ClaimFacts | null;
  missing: string[];
  citations: Citation[];
  risk: RiskSignal | null;
  riskStatus: RiskStatus;
  riskMissing: string[];
  card: ClaimCard | null;
  status: ClaimStatus;
  busy: boolean;
  error: string | null;
  lastUserText: string | null;
  history: HistoryEntry[];
}

export function initialState(): State {
  return {
    conversationId: null,
    claimId: null,
    language: "de",
    messages: [],
    facts: null,
    missing: [],
    citations: [],
    risk: null,
    riskStatus: "pending",
    riskMissing: [],
    card: null,
    status: "collecting",
    busy: false,
    error: null,
    lastUserText: null,
    history: [],
  };
}

let counter = 0;
const nextId = () => `m${++counter}`;

export function loadConversation(state: State, conv: Conversation): void {
  state.conversationId = conv.id;
  state.claimId = conv.claim_id;
  state.language = conv.language;
  state.status = conv.status;
  state.messages = conv.messages.map((m) => ({ id: m.id, role: m.role, content: m.content }));
  state.card = conv.card;
  state.facts = conv.card?.facts ?? null;
  state.citations = conv.card?.citations ?? [];
  state.risk = conv.card?.risk ?? null;
  state.riskStatus = conv.card?.risk_status ?? (state.risk ? "available" : "pending");
  state.riskMissing = conv.card?.risk_missing ?? [];
  state.history = conv.history ?? [];
  state.missing = conv.missing ?? [];
}

export function beginTurn(state: State, text: string): void {
  if (state.status === "information_needed" || state.card?.assessment_stale) {
    state.status = "collecting";
    state.card = null;
    state.citations = [];
    state.risk = null;
    state.riskStatus = "pending";
    state.riskMissing = [];
  }
  state.messages.push({ id: nextId(), role: "user", content: text });
  state.messages.push({ id: nextId(), role: "assistant", content: "", streaming: true });
  state.busy = true;
  state.error = null;
  state.lastUserText = text;
}

function streamingBubble(state: State): ChatItem | undefined {
  return [...state.messages].reverse().find((m) => m.streaming);
}

export function reduce(state: State, event: AgentEvent): void {
  switch (event.type) {
    case "facts":
      state.facts = event.data.facts;
      state.language = event.data.language ?? state.language;
      break;
    case "missing":
      state.missing = event.data.missing;
      break;
    case "token": {
      const bubble = streamingBubble(state);
      if (bubble) bubble.content += event.data.text;
      break;
    }
    case "question": {
      const bubble = streamingBubble(state);
      if (bubble) bubble.content = event.data.text;
      break;
    }
    case "citations":
      state.citations = event.data.citations;
      break;
    case "risk_availability":
      state.riskStatus = event.data.status;
      state.riskMissing = event.data.missing;
      if (event.data.status !== "available") state.risk = null;
      break;
    case "risk":
      state.risk = event.data.risk;
      if (state.risk) state.riskStatus = "available";
      break;
    case "card": {
      state.card = event.data.card;
      state.facts = event.data.card.facts;
      state.citations = event.data.card.citations;
      state.risk = event.data.card.risk;
      state.riskStatus = event.data.card.risk_status ?? (state.risk ? "available" : "pending");
      state.riskMissing = event.data.card.risk_missing ?? [];
      state.status = event.data.card.status;
      const bubble = streamingBubble(state);
      if (bubble && !bubble.content) bubble.content = event.data.card.coverage_summary;
      break;
    }
    case "done":
      state.status = event.data.status;
      state.claimId = event.data.claim_id;
      finishTurn(state);
      break;
    case "error":
      state.error = event.data.message;
      finishTurn(state);
      break;
  }
}

export function finishTurn(state: State): void {
  for (const m of state.messages) if (m.streaming) m.streaming = false;
  state.messages = state.messages.filter((m) => m.role !== "assistant" || m.content.length > 0);
  state.busy = false;
}

export function applyReview(state: State, status: ClaimStatus, card: ClaimCard, history?: HistoryEntry[], missing?: string[]): void {
  state.status = status;
  state.card = card;
  state.facts = card.facts;
  state.citations = card.citations;
  state.risk = card.risk;
  state.riskStatus = card.risk_status ?? (state.risk ? "available" : "pending");
  state.riskMissing = card.risk_missing ?? [];
  if (history) state.history = history;
  if (missing) state.missing = missing;
}

export const store = reactive(initialState());
