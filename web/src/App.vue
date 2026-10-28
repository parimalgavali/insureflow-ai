<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { locale, setLocale, t } from "./i18n";
import { createConversation, reviewClaim, sendMessage, type Language } from "./api/client";
import ChatColumn from "./components/ChatColumn.vue";
import ClaimCard from "./components/ClaimCard.vue";
import EvalPage from "./components/EvalPage.vue";
import { applyReview, beginTurn, finishTurn, loadConversation, reduce, store } from "./store";

const showEval = ref(location.hash === "#eval");
window.addEventListener("hashchange", () => (showEval.value = location.hash === "#eval"));

const canSend = computed(() => store.conversationId !== null && store.status !== "reviewed");

async function start(language: Language) {
  try {
    loadConversation(store, await createConversation(language));
  } catch (e) {
    store.error = (e as Error).message;
  }
}

async function send(text: string, file: File | null) {
  if (!store.conversationId) return;
  beginTurn(store, text);
  try {
    await sendMessage(store.conversationId, text, file, (event) => reduce(store, event), store.language);
  } catch (e) {
    store.error = (e as Error).message;
    finishTurn(store);
  }
}

async function review(patch: Record<string, unknown>) {
  if (!store.claimId) return;
  store.busy = true;
  try {
    const decision = Object.keys(patch).length ? { decision: "edit" as const, facts_patch: patch } : { decision: "accept" as const };
    const result = await reviewClaim(store.claimId, decision);
    applyReview(store, result.status, result.card);
  } catch (e) {
    store.error = (e as Error).message;
  } finally {
    store.busy = false;
  }
}

function retry() {
  store.error = null;
  if (!store.conversationId) return start(store.language);
  const last = store.lastUserText;
  store.messages = store.messages.filter((m) => !(m.role === "user" && m.content === last && m === store.messages.at(-1)));
  if (last) return send(last, null);
}

async function switchLanguage(lang: Language) {
  setLocale(lang);
  const hasUserMessages = store.messages.some((m) => m.role === "user");
  if (!hasUserMessages) return start(lang); // fresh greeting in the new language
  store.language = lang; // agent follows the toggle from the next message on
}

onMounted(() => start(locale.value));
</script>

<template>
  <div class="app">
    <header>
      <div>
        <h1>{{ t("app.title") }}</h1>
        <p>{{ t("app.tagline") }}</p>
      </div>
      <div class="meta">
        <div class="lang" role="group" :aria-label="t('app.language')">
          <button v-for="l in ['de', 'en'] as const" :key="l" type="button" class="chip" :class="{ active: locale === l }" :aria-pressed="locale === l" :data-testid="`lang-${l}`" @click="switchLanguage(l)">
            {{ l.toUpperCase() }}
          </button>
        </div>
        <p v-if="store.conversationId"><small>{{ t("app.conversation") }} {{ store.conversationId.slice(0, 8) }} · <a :href="showEval ? '#' : '#eval'" data-testid="eval-link">{{ showEval ? t("app.backToClaim") : t("app.evalLink") }}</a></small></p>
      </div>
    </header>
    <EvalPage v-if="showEval" />
    <template v-else>
    <ChatColumn :messages="store.messages" :missing="store.missing" :busy="store.busy" :error="store.error" :can-send="canSend" @send="send" @retry="retry" />
    <ClaimCard :facts="store.facts" :missing="store.missing" :citations="store.citations" :risk="store.risk" :card="store.card" :status="store.status" :busy="store.busy" @review="review" />
    </template>
  </div>
</template>
