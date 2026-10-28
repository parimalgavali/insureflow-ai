<script setup lang="ts">
import { computed, onMounted } from "vue";
import { createConversation, reviewClaim, sendMessage, type Language } from "./api/client";
import ChatColumn from "./components/ChatColumn.vue";
import ClaimCard from "./components/ClaimCard.vue";
import { applyReview, beginTurn, finishTurn, loadConversation, reduce, store } from "./store";

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
    await sendMessage(store.conversationId, text, file, (event) => reduce(store, event));
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

onMounted(() => start(navigator.language.toLowerCase().startsWith("de") ? "de" : "en"));
</script>

<template>
  <div class="app">
    <header>
      <div>
        <h1>ClaimPilot</h1>
        <p>File a motor claim by chat. Answers cite the GDV AKB 2015 model terms; a human adjuster reviews every case.</p>
      </div>
      <p v-if="store.conversationId"><small>conversation {{ store.conversationId.slice(0, 8) }} · {{ store.language.toUpperCase() }}</small></p>
    </header>
    <ChatColumn :messages="store.messages" :missing="store.missing" :busy="store.busy" :error="store.error" :can-send="canSend" @send="send" @retry="retry" />
    <ClaimCard :facts="store.facts" :missing="store.missing" :citations="store.citations" :risk="store.risk" :card="store.card" :status="store.status" :busy="store.busy" @review="review" />
  </div>
</template>
