<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { locale, setLocale, t } from "./i18n";
import { createConversation, decideEvidenceSuggestion, extractEvidence, replaceEvidencePdf, linkChecklistFile, sendMessage, submitClaim, correctClaimFacts, refreshClaimAssessment, getConversation, setAccessToken, retrySavedMessage, type EvidenceDecision, type DocumentType, type Language, type ReviewerClaim } from "./api/client";
import ChatColumn from "./components/ChatColumn.vue";
import PolicyUpload from "./components/PolicyUpload.vue";
import ClaimCard from "./components/ClaimCard.vue";
import EvalPage from "./components/EvalPage.vue";
import ReviewerQueue from "./components/ReviewerQueue.vue";
import HistoryPage from "./components/HistoryPage.vue";
import { evidenceErrorCode, evidenceReplacementProblem, pdfProblem } from "./evidenceMessages";
import { currentClaim, rememberClaim } from "./currentClaim";
import { applyReview, beginTurn, finishTurn, loadConversation, initialState, reduce, store } from "./store";

const showEval = ref(location.hash === "#eval");
const showReviewer = ref(location.hash === "#review");
const historyId = ref(location.hash.startsWith("#history/") ? location.hash.slice(9) : null);
const retrySubmission = ref(false);
const retryExtraction = ref<string | null>(null);
const retryChecklist = ref<{ itemId: string; attachmentId: string; linked: boolean } | null>(null);
const retryReplacement = ref<{ id: string; file: File } | null>(null);
const retryDecision = ref<{ id: string; decision: EvidenceDecision } | null>(null);
const pendingEvidence = computed(() => store.attachments.flatMap((attachment) => attachment.suggestions || []).find((suggestion) => suggestion.status === "applying"));
const hasPendingEvidence = computed(() => !!pendingEvidence.value || !!retryDecision.value);
const opening = ref(false);
const policyBusy = ref(false);
const openError = ref(false);
const accessDraft = ref("");
let openVersion = 0;
const messageNeedsRetry = ref(false);
const restoredDraft = ref<{ text: string; file: File | null; documentType: DocumentType } | null>(null);
const validationError = ref(false);
let pendingMessage: { text: string; file: File | null; documentType: DocumentType; language: Language; id: string; before: typeof store.messages; beforeView: Pick<typeof store, "status" | "card" | "citations" | "risk" | "riskStatus" | "riskMissing" | "lastUserText"> } | null = null;
const retryCorrection = ref<{ patch: Record<string, unknown>; refresh: boolean } | null>(null);
function navigate() {
  showEval.value = location.hash === "#eval";
  showReviewer.value = location.hash === "#review";
  historyId.value = location.hash.startsWith("#history/") ? location.hash.slice(9) : null;
  if (!showEval.value && !showReviewer.value && !historyId.value && !store.conversationId) start(locale.value);
}
window.addEventListener("hashchange", navigate);
onUnmounted(() => { window.removeEventListener("hashchange", navigate); openVersion++; accessDraft.value = ""; setAccessToken(""); });

const canSend = computed(() => store.conversationId !== null && !opening.value && !openError.value && !policyBusy.value && !messageNeedsRetry.value && !hasPendingEvidence.value && !retryReplacement.value && !retryChecklist.value && ["collecting", "information_needed"].includes(store.status));

async function start(language: Language, forceNew = false) {
  if (opening.value || store.busy || policyBusy.value) return;
  const version = ++openVersion;
  opening.value = true;
  openError.value = false;
  try {
    const saved = forceNew ? null : currentClaim();
    const conversation = saved ? await getConversation(saved) : await createConversation(language);
    if (version !== openVersion) return;
    Object.assign(store, initialState());
    loadConversation(store, conversation);
    rememberClaim(conversation.id);
    pendingMessage = null;
    retryExtraction.value = null;
    retryDecision.value = null;
    retryReplacement.value = null;
    retryChecklist.value = null;
    restoredDraft.value = null;
    validationError.value = false;
    retryCorrection.value = null;
    retrySubmission.value = false;
    messageNeedsRetry.value = !!store.pendingOperationId;
    if (store.pendingOperationId) store.error = t("session.pending");
  } catch {
    if (version === openVersion) openError.value = true;
  } finally {
    if (version === openVersion) opening.value = false;
  }
}

function retryOpen() {
  if (accessDraft.value.trim()) setAccessToken(accessDraft.value);
  accessDraft.value = "";
  return start(locale.value);
}

async function onPolicyChanged(conversationId: string) {
  if (store.conversationId !== conversationId) return;
  store.busy = true;
  try {
    const conversation = await getConversation(conversationId);
    if (store.conversationId === conversationId) loadConversation(store, conversation);
  } catch {
    openError.value = true;
  } finally {
    store.busy = false;
  }
}

async function send(text: string, file: File | null, documentType: DocumentType = "other_document", retrying = false) {
  if (!store.conversationId || store.busy || (pendingMessage && !retrying)) return;
  validationError.value = false;
  restoredDraft.value = null;
  retryCorrection.value = null;
  retryExtraction.value = null;
  retrySubmission.value = false;
  if (!retrying || !pendingMessage) {
    pendingMessage = { text, file, documentType, language: store.language, id: crypto.randomUUID(), before: store.messages.map((m) => ({ ...m })), beforeView: { status: store.status, card: store.card, citations: store.citations, risk: store.risk, riskStatus: store.riskStatus, riskMissing: store.riskMissing, lastUserText: store.lastUserText } };
  } else {
    store.messages = pendingMessage.before.map((m) => ({ ...m }));
  }
  const operation = pendingMessage;
  beginTurn(store, operation.text);
  try {
    await sendMessage(store.conversationId, operation.text, operation.file, (event) => {
      reduce(store, event.type === "error" ? { type: "error", data: { message: t("chat.sendFailed") } } : event);
      store.busy = true; // Keep the turn locked until canonical state has been restored.
    }, operation.language, operation.id, operation.documentType);
    if (!store.error) {
      loadConversation(store, await getConversation(store.conversationId));
      pendingMessage = null;
      messageNeedsRetry.value = false;
    }
  } catch (error) {
    const status = error instanceof Error ? /^(413|415|422) /.exec(error.message)?.[1] : null;
    if (status) {
      store.messages = operation.before.map((m) => ({ ...m }));
      Object.assign(store, operation.beforeView);
      restoredDraft.value = { text: operation.text, file: operation.file, documentType: operation.documentType };
      pendingMessage = null;
      validationError.value = true;
      const problem = status === "422" ? pdfProblem(evidenceErrorCode(error)) : null;
      store.error = problem ? `${problem} ${t("evidence.draftRestored")}` : t(status === "413" ? "evidence.uploadTooLarge" : status === "415" ? "evidence.uploadUnsupported" : "evidence.uploadInvalid");
    } else store.error = t("chat.sendFailed");
  } finally {
    if (store.error && !validationError.value) {
      // A saved upload remains visible even when assessment or streaming failed.
      try {
        const saved = await getConversation(store.conversationId);
        store.attachments = saved.attachments ?? [];
        store.documentChecklist = saved.document_checklist ?? [];
      } catch { /* Retry keeps the original operation. */ }
    }
    messageNeedsRetry.value = !!store.error && !validationError.value;
    finishTurn(store);
  }
}

async function readEvidence(attachmentId: string) {
  if (!store.conversationId || store.busy || messageNeedsRetry.value || policyBusy.value || hasPendingEvidence.value || retryReplacement.value || retryChecklist.value) return;
  store.busy = true;
  store.error = null;
  validationError.value = false;
  retryCorrection.value = null;
  retrySubmission.value = false;
  retryExtraction.value = attachmentId;
  try {
    const result = await extractEvidence(store.conversationId, attachmentId);
    store.attachments = store.attachments.map((attachment) => attachment.id === result.id ? result : attachment);
    retryExtraction.value = null;
  } catch {
    store.error = t("evidence.readFailed");
  } finally {
    store.busy = false;
  }
}

async function linkDocument(itemId: string, attachmentId: string, linked: boolean) {
  if (!store.claimId || store.busy || policyBusy.value || messageNeedsRetry.value || hasPendingEvidence.value || retryReplacement.value) return;
  if (retryCorrection.value || retrySubmission.value || retryExtraction.value) {
    store.error = t("evidence.finishPrevious"); validationError.value = false; return;
  }
  store.busy = true; store.error = null; validationError.value = false;
  retryChecklist.value = { itemId, attachmentId, linked };
  try {
    const result = await linkChecklistFile(store.claimId, itemId, attachmentId, linked);
    applyReview(store, result.status, result.card, result.history, result.missing, result.attachments, result.document_checklist);
    retryChecklist.value = null;
  } catch (error) {
    try { if (store.conversationId) loadConversation(store, await getConversation(store.conversationId)); } catch { /* Retry the same link. */ }
    if (error instanceof Error && /^(409|422|404) /.test(error.message)) { retryChecklist.value = null; validationError.value = true; }
    store.error = t("checklist.linkFailed");
  } finally { store.busy = false; }
}

async function replaceEvidence(attachmentId: string, file: File) {
  if (!store.conversationId || store.busy || policyBusy.value || messageNeedsRetry.value || hasPendingEvidence.value || retryChecklist.value) return;
  if (retryCorrection.value || retrySubmission.value || retryExtraction.value) {
    store.error = t("evidence.finishPrevious"); validationError.value = false; return;
  }
  store.busy = true;
  store.error = null;
  validationError.value = false;
  retryReplacement.value = { id: attachmentId, file };
  try {
    await replaceEvidencePdf(store.conversationId, attachmentId, file);
    loadConversation(store, await getConversation(store.conversationId));
    retryReplacement.value = null;
  } catch (error) {
    try { loadConversation(store, await getConversation(store.conversationId)); } catch { /* Keep the original copy for retry. */ }
    if (error instanceof Error && /^(409|413|415|422) /.test(error.message)) {
      retryReplacement.value = null;
      validationError.value = true;
    }
    store.error = evidenceReplacementProblem(error);
  } finally {
    store.busy = false;
  }
}

async function decideEvidence(suggestionId: string, decision: EvidenceDecision) {
  if (!store.claimId || store.busy || messageNeedsRetry.value || policyBusy.value || retryReplacement.value || retryChecklist.value) return;
  if (retryCorrection.value || retrySubmission.value || retryExtraction.value) {
    store.error = t("evidence.finishPrevious");
    validationError.value = false;
    return;
  }
  store.busy = true;
  store.error = null;
  validationError.value = false;
  retryExtraction.value = null;
  retryCorrection.value = null;
  retrySubmission.value = false;
  retryDecision.value = { id: suggestionId, decision };
  try {
    const result = await decideEvidenceSuggestion(store.claimId, suggestionId, decision);
    applyReview(store, result.status, result.card, result.history, result.missing, result.attachments, result.document_checklist);
    if (store.conversationId) loadConversation(store, await getConversation(store.conversationId));
    retryDecision.value = null;
  } catch (error) {
    try { if (store.conversationId) loadConversation(store, await getConversation(store.conversationId)); } catch { /* Keep this exact decision for retry. */ }
    if (error instanceof Error && error.message.startsWith("409 ")) {
      retryDecision.value = null;
      validationError.value = true;
      store.error = t("evidence.changed");
    } else store.error = t("evidence.decisionFailed");
  } finally {
    store.busy = false;
  }
}

function finishEvidenceDecision() {
  if (retryDecision.value) return decideEvidence(retryDecision.value.id, retryDecision.value.decision);
  const suggestion = pendingEvidence.value;
  if (suggestion) return decideEvidence(suggestion.id, { decision: "accept", expected_current: suggestion.expected_value ?? null, replace_existing: true });
}

async function submit() {
  if (!store.claimId || store.busy) return;
  store.busy = true;
  retryCorrection.value = null;
  retryExtraction.value = null;
  store.error = null;
  validationError.value = false;
  try {
    const result = await submitClaim(store.claimId);
    applyReview(store, result.status, result.card, result.history, result.missing, result.attachments, result.document_checklist);
    retrySubmission.value = false;
  } catch (e) {
    store.error = (e as Error).message;
    retrySubmission.value = true;
  } finally {
    store.busy = false;
  }
}

function onReviewed(claim: ReviewerClaim) {
  if (claim.id === store.claimId && claim.card) applyReview(store, claim.status, claim.card, claim.history, claim.missing, claim.attachments, claim.document_checklist);
}

async function correct(patch: Record<string, unknown> = {}, refresh = false) {
  if (!store.claimId || store.busy) return;
  store.busy = true;
  store.error = null;
  validationError.value = false;
  retrySubmission.value = false;
  retryExtraction.value = null;
  retryCorrection.value = { patch, refresh };
  try {
    const result = refresh ? await refreshClaimAssessment(store.claimId) : await correctClaimFacts(store.claimId, patch);
    applyReview(store, result.status, result.card, result.history, result.missing, result.attachments, result.document_checklist);
    if (store.conversationId) loadConversation(store, await getConversation(store.conversationId));
    retryCorrection.value = null;
  } catch (e) {
    store.error = e instanceof Error && e.message.startsWith("422 ") ? t("customer.invalidCorrection") : (e as Error).message;
  } finally {
    store.busy = false;
  }
}

async function resumeSavedMessage() {
  if (!store.conversationId || !store.pendingOperationId || store.busy) return;
  store.busy = true;
  store.error = null;
  validationError.value = false;
  try {
    await retrySavedMessage(store.conversationId, store.pendingOperationId, (event) => {
      reduce(store, event.type === "error" ? { type: "error", data: { message: t("chat.sendFailed") } } : event);
      store.busy = true;
    });
    if (!store.error) loadConversation(store, await getConversation(store.conversationId));
  } catch {
    store.error = t("chat.sendFailed");
  } finally {
    messageNeedsRetry.value = !!store.pendingOperationId || !!store.error;
    finishTurn(store);
  }
}

function retry() {
  if (retryChecklist.value) return linkDocument(retryChecklist.value.itemId, retryChecklist.value.attachmentId, retryChecklist.value.linked);
  if (retryReplacement.value) return replaceEvidence(retryReplacement.value.id, retryReplacement.value.file);
  store.error = null;
  validationError.value = false;
  if (retryDecision.value) return decideEvidence(retryDecision.value.id, retryDecision.value.decision);
  if (retryExtraction.value) return readEvidence(retryExtraction.value);
  if (retrySubmission.value) return submit();
  if (retryCorrection.value) return correct(retryCorrection.value.patch, retryCorrection.value.refresh);
  if (!store.conversationId) return start(store.language);
  if (pendingMessage) return send(pendingMessage.text, pendingMessage.file, pendingMessage.documentType, true);
  if (store.pendingOperationId) return resumeSavedMessage();
}

async function switchLanguage(lang: Language) {
  setLocale(lang);
  if (showReviewer.value || showEval.value || historyId.value) return;
  const hasUserMessages = store.messages.some((m) => m.role === "user");
  if (!hasUserMessages && !openError.value) return start(lang, true); // fresh greeting in the new language
  store.language = lang; // agent follows the toggle from the next message on
}

onMounted(() => {
  if (!showReviewer.value && !showEval.value && !historyId.value) start(locale.value);
});
</script>

<template>
  <div class="app">
    <header>
      <div>
        <h1>{{ t("app.title") }}</h1>
        <p>{{ t("app.tagline") }}</p>
      </div>
      <div class="meta">
        <nav>
          <a :href="showReviewer ? '#' : '#review'" data-testid="reviewer-link">{{ showReviewer ? t("app.backToClaim") : t("queue.title") }}</a>
        </nav>
        <div class="lang" role="group" :aria-label="t('app.language')">
          <button v-for="l in ['de', 'en'] as const" :key="l" type="button" class="chip" :class="{ active: locale === l }" :aria-pressed="locale === l" :data-testid="`lang-${l}`" @click="switchLanguage(l)">
            {{ l.toUpperCase() }}
          </button>
        </div>
        <p v-if="store.conversationId"><small>{{ t("app.conversation") }} {{ store.conversationId.slice(0, 8) }} · <a :href="showEval ? '#' : '#eval'" data-testid="eval-link">{{ showEval ? t("app.backToClaim") : t("app.evalLink") }}</a></small></p>
      </div>
    </header>
    <ReviewerQueue v-if="showReviewer" @reviewed="onReviewed" />
    <EvalPage v-else-if="showEval" />
    <HistoryPage v-else-if="historyId" :claim-id="historyId" />
    <template v-else>
    <section class="panel claim-session" data-testid="claim-session">
      <p v-if="opening" role="status">{{ t("session.loading") }}</p>
      <div v-if="openError" role="alert">
        <p>{{ t("session.unavailable") }}</p>
        <form @submit.prevent="retryOpen">
          <label for="claim-access">{{ t("session.access") }}</label>
          <input id="claim-access" v-model="accessDraft" type="password" autocomplete="off" :disabled="opening" />
          <p>{{ t("session.memory") }}</p>
          <button class="btn" :disabled="opening">{{ t("chat.retry") }}</button>
        </form>
      </div>
      <button class="btn" data-testid="new-claim" :disabled="opening || store.busy || policyBusy" @click="start(locale, true)">{{ t("session.new") }}</button>
      <p>{{ t("session.newNote") }}</p>
    </section>
    <section v-if="hasPendingEvidence && !openError && !opening" class="panel" role="status" data-testid="pending-evidence-decision">
      <p>{{ t("evidence.pendingDecision") }}</p>
      <button class="btn" :disabled="store.busy" @click="finishEvidenceDecision">{{ t("evidence.finishDecision") }}</button>
    </section>
    <PolicyUpload v-if="store.conversationId && !openError && !opening" :key="store.conversationId" :conversation-id="store.conversationId" :busy="store.busy || messageNeedsRetry || hasPendingEvidence || !!retryReplacement || !!retryChecklist" :can-upload="['collecting', 'assessed', 'information_needed'].includes(store.status)" @busy="policyBusy = $event" @changed="onPolicyChanged" />
    <ChatColumn v-if="!openError && !opening" :key="store.conversationId || 'new'" :messages="store.messages" :missing="store.missing" :busy="store.busy" :error="store.error" :can-send="canSend" :restored-draft="restoredDraft" :retryable="!validationError" @send="send" @retry="retry" />
    <ClaimCard v-if="!openError && !opening" :key="store.conversationId || 'new'" :facts="store.facts" :missing="store.missing" :citations="store.citations" :risk="store.risk" :risk-status="store.riskStatus" :risk-missing="store.riskMissing" :card="store.card" :status="store.status" :busy="store.busy || messageNeedsRetry || policyBusy || hasPendingEvidence || !!retryReplacement || !!retryChecklist" :claim-id="store.claimId" :history="store.history" :attachments="store.attachments" :checklist="store.documentChecklist" @link-document="linkDocument" @replace-evidence="replaceEvidence" @decide-evidence="decideEvidence" @extract-evidence="readEvidence" @submit="submit" @customer-correct="correct" @customer-refresh="correct({}, true)" />
    </template>
  </div>
</template>
