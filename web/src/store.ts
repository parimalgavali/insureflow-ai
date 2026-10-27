/** One reactive store; every SSE event is reduced here so components stay dumb. */
import { reactive } from "vue";
import type { AgentEvent, Citation, ClaimCard, ClaimFacts, ClaimStatus, Conversation, Language, RiskSignal } from "./api/client";

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
  card: ClaimCard | null;
  status: ClaimStatus;
  busy: boolean;
  error: string | null;
  lastUserText: string | null;
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
    card: null,
    status: "collecting",
    busy: false,
    error: null,
    lastUserText: null,
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
}

export function beginTurn(state: State, text: string): void {
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
    case "risk":
      state.risk = event.data.risk;
      break;
    case "card": {
      state.card = event.data.card;
      state.facts = event.data.card.facts;
      state.citations = event.data.card.citations;
      state.risk = event.data.card.risk;
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

export function applyReview(state: State, status: ClaimStatus, card: ClaimCard): void {
  state.status = status;
  state.card = card;
  state.facts = card.facts;
}

export const store = reactive(initialState());
