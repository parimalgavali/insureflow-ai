<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { locale, setLocale, t } from "./i18n";
import { createConversation, sendMessage, submitClaim, correctClaimFacts, refreshClaimAssessment, getConversation, type Language, type ReviewerClaim } from "./api/client";
import ChatColumn from "./components/ChatColumn.vue";
import ClaimCard from "./components/ClaimCard.vue";
import EvalPage from "./components/EvalPage.vue";
import ReviewerQueue from "./components/ReviewerQueue.vue";
import HistoryPage from "./components/HistoryPage.vue";
import { applyReview, beginTurn, finishTurn, loadConversation, reduce, store } from "./store";

const showEval = ref(location.hash === "#eval");
const showReviewer = ref(location.hash === "#review");
const historyId = ref(location.hash.startsWith("#history/") ? location.hash.slice(9) : null);
const retrySubmission = ref(false);
const retryCorrection = ref<{ patch: Record<string, unknown>; refresh: boolean } | null>(null);
function navigate() {
  showEval.value = location.hash === "#eval";
  showReviewer.value = location.hash === "#review";
  historyId.value = location.hash.startsWith("#history/") ? location.hash.slice(9) : null;
  if (!showEval.value && !showReviewer.value && !historyId.value && !store.conversationId) start(locale.value);
}
window.addEventListener("hashchange", navigate);
onUnmounted(() => window.removeEventListener("hashchange", navigate));

const canSend = computed(() => store.conversationId !== null && ["collecting", "information_needed"].includes(store.status));

async function start(language: Language) {
  try {
    loadConversation(store, await createConversation(language));
  } catch (e) {
    store.error = (e as Error).message;
  }
}

async function send(text: string, file: File | null) {
  if (!store.conversationId) return;
  retryCorrection.value = null;
  retrySubmission.value = false;
  beginTurn(store, text);
  try {
    await sendMessage(store.conversationId, text, file, (event) => reduce(store, event), store.language);
  } catch (e) {
    store.error = (e as Error).message;
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

function retry() {
  store.error = null;
  if (retrySubmission.value) return submit();
  if (retryCorrection.value) return correct(retryCorrection.value.patch, retryCorrection.value.refresh);
  if (!store.conversationId) return start(store.language);
  const last = store.lastUserText;
  store.messages = store.messages.filter((m) => !(m.role === "user" && m.content === last && m === store.messages.at(-1)));
  if (last) return send(last, null);
}

async function switchLanguage(lang: Language) {
  setLocale(lang);
  if (showReviewer.value || showEval.value || historyId.value) return;
  const hasUserMessages = store.messages.some((m) => m.role === "user");
  if (!hasUserMessages) return start(lang); // fresh greeting in the new language
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
    <ChatColumn :messages="store.messages" :missing="store.missing" :busy="store.busy" :error="store.error" :can-send="canSend" @send="send" @retry="retry" />
    <ClaimCard :facts="store.facts" :missing="store.missing" :citations="store.citations" :risk="store.risk" :risk-status="store.riskStatus" :risk-missing="store.riskMissing" :card="store.card" :status="store.status" :busy="store.busy" :claim-id="store.claimId" :history="store.history" @submit="submit" @customer-correct="correct" @customer-refresh="correct({}, true)" />
    </template>
  </div>
</template>
