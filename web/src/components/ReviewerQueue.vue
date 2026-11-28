<script setup lang="ts">
import { onUnmounted, ref } from "vue";
import { fetchReviewQueue, fetchReviewerClaim, reviewClaim, type QueueItem, type ReviewerClaim, type ReviewDecision } from "../api/client";
import { locale, t } from "../i18n";
import ClaimCard from "./ClaimCard.vue";

const emit = defineEmits<{ reviewed: [claim: ReviewerClaim] }>();
const draftToken = ref("");
const credential = ref("");
const items = ref<QueueItem[]>([]);
const selected = ref<ReviewerClaim | null>(null);
const busy = ref(false);
const error = ref("");
const hasMore = ref(false);
let epoch = 0;

function lock() {
  epoch++;
  credential.value = "";
  draftToken.value = "";
  items.value = [];
  selected.value = null;
  hasMore.value = false;
  busy.value = false;
}

function failure(e: unknown) {
  // Remove protected data as well as the credential on any failed reviewer request.
  lock();
  error.value = e instanceof Error ? e.message : t("queue.failed");
}

async function load(append = false) {
  if (busy.value) return;
  if (!credential.value) {
    credential.value = draftToken.value.trim();
    draftToken.value = "";
  }
  if (!credential.value) return;
  const current = epoch;
  busy.value = true;
  error.value = "";
  try {
    const result = await fetchReviewQueue(credential.value, append ? items.value.length : 0);
    if (current !== epoch) return;
    items.value = append ? [...items.value, ...result.items] : result.items;
    hasMore.value = result.has_more;
  } catch (e) {
    if (current === epoch) failure(e);
  } finally {
    if (current === epoch) busy.value = false;
  }
}

async function selectClaim(id: string) {
  if (busy.value) return;
  const current = epoch;
  busy.value = true;
  selected.value = null;
  error.value = "";
  try {
    const result = await fetchReviewerClaim(id, credential.value);
    if (current === epoch) selected.value = result;
  } catch (e) {
    if (current === epoch) failure(e);
  } finally {
    if (current === epoch) busy.value = false;
  }
}

async function saveDecision(decision: ReviewDecision) {
  if (!selected.value || busy.value) return;
  const current = epoch;
  const claim = selected.value;
  busy.value = true;
  error.value = "";
  try {
    const result = await reviewClaim(claim.id, decision, () => credential.value);
    if (current !== epoch) return;
    selected.value = { ...claim, ...result };
    emit("reviewed", selected.value);
    const queue = await fetchReviewQueue(credential.value);
    if (current !== epoch) return;
    items.value = queue.items;
    hasMore.value = queue.has_more;
  } catch (e) {
    if (current === epoch) {
      if (e instanceof Error && e.message.startsWith("422 ")) error.value = t("queue.invalidCorrection");
      else failure(e);
    }
  } finally {
    if (current === epoch) busy.value = false;
  }
}

function review(patch: Record<string, unknown>, note?: string) {
  return saveDecision({ decision: Object.keys(patch).length ? "edit" : "accept", facts_patch: patch, ...(note ? { note } : {}) });
}

function requestInfo(note: string) {
  return saveDecision({ decision: "request_info", note });
}

function reassess() {
  return saveDecision({ decision: "reassess" });
}

function submittedAt(value: string | null): string {
  return value ? new Date(value).toLocaleString(locale.value) : t("queue.dateUnknown");
}

onUnmounted(lock);
</script>

<template>
  <section class="reviewer-workspace" :aria-label="t('queue.title')">
    <div class="panel queue-list">
      <h2>{{ t("queue.title") }}</h2>
      <p>{{ t("queue.help") }}</p>
      <form v-if="!credential" @submit.prevent="load()">
        <label for="reviewer-credential">{{ t("queue.token") }}</label>
        <input id="reviewer-credential" v-model="draftToken" type="password" autocomplete="off" :disabled="busy" />
        <button class="btn primary" :disabled="busy || !draftToken.trim()">{{ t("queue.open") }}</button>
      </form>
      <div v-else class="review">
        <button class="btn" :disabled="busy" @click="load()">{{ t("queue.refresh") }}</button>
        <button class="btn" @click="lock()">{{ t("queue.lock") }}</button>
      </div>
      <p v-if="busy" role="status">{{ t("queue.loading") }}</p>
      <p v-if="error" role="alert">{{ error }}</p>
      <template v-if="credential">
        <p v-if="!busy && !items.length">{{ t("queue.empty") }}</p>
        <ul class="queue-items">
          <li v-for="item in items" :key="item.id">
            <button class="btn" :disabled="busy" :aria-pressed="selected?.id === item.id" :data-testid="`review-claim-${item.id}`" @click="selectClaim(item.id)">
              <strong>{{ item.id.slice(0, 8) }} · {{ item.event_type }}</strong>
              <span>{{ item.location || t("queue.locationUnknown") }}</span>
              <span>{{ t("queue.submitted") }}: {{ submittedAt(item.submitted_at) }}</span>
            </button>
          </li>
        </ul>
        <button v-if="hasMore" class="btn" :disabled="busy" @click="load(true)">{{ t("queue.more") }}</button>
      </template>
    </div>
    <ClaimCard v-if="selected?.card" :key="selected.id" :facts="selected.card.facts" :missing="selected.missing || []" :citations="selected.card.citations" :risk="selected.card.risk" :card="selected.card" :status="selected.status" :busy="busy" :claim-id="selected.id" :history="selected.history || []" reviewer @review="review" @request-info="requestInfo" @reassess="reassess" />
    <p v-else-if="credential && !busy" class="panel queue-list">{{ t("queue.choose") }}</p>
  </section>
</template>
