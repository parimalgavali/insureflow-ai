<script setup lang="ts">
import { onUnmounted, ref, watch } from "vue";
import { fetchClaimHistory, type HistoryEntry } from "../api/client";
import { t } from "../i18n";
import ClaimHistory from "./ClaimHistory.vue";

const props = defineProps<{ claimId: string }>();
const entries = ref<HistoryEntry[]>([]);
const error = ref("");
const loading = ref(false);
const accessToken = ref("");
let version = 0;

async function load() {
  const current = ++version;
  entries.value = [];
  error.value = "";
  loading.value = true;
  try {
    const token = accessToken.value.trim();
    const result = token ? await fetchClaimHistory(props.claimId, token) : await fetchClaimHistory(props.claimId);
    if (current === version) entries.value = result;
  } catch {
    if (current === version) error.value = t("history.loadFailed");
  } finally {
    if (current === version) loading.value = false;
  }
}

watch(() => props.claimId, load, { immediate: true });
onUnmounted(() => { version++; accessToken.value = ""; });
</script>

<template>
  <section class="panel history-page">
    <h2>{{ t("history.title") }}</h2>
    <p>{{ t("history.claim") }}: {{ claimId }}</p>
    <a href="#">{{ t("history.back") }}</a>
    <p v-if="loading" role="status">{{ t("history.loading") }}</p>
    <div v-else-if="error" role="alert">
      <p>{{ error }}</p>
      <form class="history-access" @submit.prevent="load">
        <label for="history-access-token">{{ t("history.accessToken") }}</label>
        <input id="history-access-token" v-model="accessToken" type="password" autocomplete="off" />
        <p class="disclaimer">{{ t("history.tokenMemory") }}</p>
        <button class="btn">{{ t("chat.retry") }}</button>
      </form>
    </div>
    <ClaimHistory v-else :entries="entries" />
  </section>
</template>
