<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { locale, setLocale, t } from "./i18n";
import { createConversation, sendMessage, submitClaim, correctClaimFacts, refreshClaimAssessment, getConversation, setAccessToken, retrySavedMessage, type Language, type ReviewerClaim } from "./api/client";
import ChatColumn from "./components/ChatColumn.vue";
import PolicyUpload from "./components/PolicyUpload.vue";
import ClaimCard from "./components/ClaimCard.vue";
import EvalPage from "./components/EvalPage.vue";
import ReviewerQueue from "./components/ReviewerQueue.vue";
import HistoryPage from "./components/HistoryPage.vue";
import { currentClaim, rememberClaim } from "./currentClaim";
import { applyReview, beginTurn, finishTurn, loadConversation, initialState, reduce, store } from "./store";

const showEval = ref(location.hash === "#eval");
const showReviewer = ref(location.hash === "#review");
const historyId = ref(location.hash.startsWith("#history/") ? location.hash.slice(9) : null);
const retrySubmission = ref(false);
const opening = ref(false);
const policyBusy = ref(false);
const openError = ref(false);
const accessDraft = ref("");
let openVersion = 0;
const messageNeedsRetry = ref(false);
let pendingMessage: { text: string; file: File | null; language: Language; id: string; before: typeof store.messages } | null = null;
const retryCorrection = ref<{ patch: Record<string, unknown>; refresh: boolean } | null>(null);
function navigate() {
  showEval.value = location.hash === "#eval";
  showReviewer.value = location.hash === "#review";
  historyId.value = location.hash.startsWith("#history/") ? location.hash.slice(9) : null;
  if (!showEval.value && !showReviewer.value && !historyId.value && !store.conversationId) start(locale.value);
}
window.addEventListener("hashchange", navigate);
onUnmounted(() => { window.removeEventListener("hashchange", navigate); openVersion++; accessDraft.value = ""; setAccessToken(""); });

const canSend = computed(() => store.conversationId !== null && !opening.value && !openError.value && !policyBusy.value && !messageNeedsRetry.value && ["collecting", "information_needed"].includes(store.status));

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

async function send(text: string, file: File | null, retrying = false) {
  if (!store.conversationId || store.busy || (pendingMessage && !retrying)) return;
  retryCorrection.value = null;
  retrySubmission.value = false;
  if (!retrying || !pendingMessage) {
    pendingMessage = { text, file, language: store.language, id: crypto.randomUUID(), before: store.messages.map((m) => ({ ...m })) };
  } else {
    store.messages = pendingMessage.before.map((m) => ({ ...m }));
  }
  const operation = pendingMessage;
  beginTurn(store, operation.text);
  try {
    await sendMessage(store.conversationId, operation.text, operation.file, (event) => {
      reduce(store, event.type === "error" ? { type: "error", data: { message: t("chat.sendFailed") } } : event);
      store.busy = true; // Keep the turn locked until canonical state has been restored.
    }, operation.language, operation.id);
    if (!store.error) {
      loadConversation(store, await getConversation(store.conversationId));
      pendingMessage = null;
      messageNeedsRetry.value = false;
    }
  } catch {
    store.error = t("chat.sendFailed");
  } finally {
    messageNeedsRetry.value = !!store.error;
    finishTurn(store);
  }
}

async function submit() {
  if (!store.claimId || store.busy) return;
  store.busy = true;
  retryCorrection.value = null;
  store.error = null;
  try {
    const result = await submitClaim(store.claimId);
    applyReview(store, result.status, result.card, result.history, result.missing);
    retrySubmission.value = false;
  } catch (e) {
    store.error = (e as Error).message;
    retrySubmission.value = true;
  } finally {
    store.busy = false;
  }
}

function onReviewed(claim: ReviewerClaim) {
  if (claim.id === store.claimId && claim.card) applyReview(store, claim.status, claim.card, claim.history, claim.missing);
}

async function correct(patch: Record<string, unknown> = {}, refresh = false) {
  if (!store.claimId || store.busy) return;
  store.busy = true;
  store.error = null;
  retrySubmission.value = false;
  retryCorrection.value = { patch, refresh };
  try {
    const result = refresh ? await refreshClaimAssessment(store.claimId) : await correctClaimFacts(store.claimId, patch);
    applyReview(store, result.status, result.card, result.history, result.missing);
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
  store.error = null;
  if (retrySubmission.value) return submit();
  if (retryCorrection.value) return correct(retryCorrection.value.patch, retryCorrection.value.refresh);
  if (!store.conversationId) return start(store.language);
  if (pendingMessage) return send(pendingMessage.text, pendingMessage.file, true);
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
    <PolicyUpload v-if="store.conversationId && !openError && !opening" :key="store.conversationId" :conversation-id="store.conversationId" :busy="store.busy || messageNeedsRetry" :can-upload="['collecting', 'assessed', 'information_needed'].includes(store.status)" @busy="policyBusy = $event" />
    <ChatColumn v-if="!openError && !opening" :key="store.conversationId || 'new'" :messages="store.messages" :missing="store.missing" :busy="store.busy" :error="store.error" :can-send="canSend" @send="send" @retry="retry" />
    <ClaimCard v-if="!openError && !opening" :key="store.conversationId || 'new'" :facts="store.facts" :missing="store.missing" :citations="store.citations" :risk="store.risk" :risk-status="store.riskStatus" :risk-missing="store.riskMissing" :card="store.card" :status="store.status" :busy="store.busy || messageNeedsRetry || policyBusy" :claim-id="store.claimId" :history="store.history" @submit="submit" @customer-correct="correct" @customer-refresh="correct({}, true)" />
    </template>
  </div>
</template>
