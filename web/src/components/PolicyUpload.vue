<script setup lang="ts">
import { onUnmounted, ref, watch } from "vue";
import { fetchPolicy, uploadPolicy, preparePolicy, type PolicySelection } from "../api/client";
import { t } from "../i18n";

const props = defineProps<{ conversationId: string; busy: boolean; canUpload: boolean }>();
const emit = defineEmits<{ busy: [value: boolean]; changed: [conversationId: string] }>();
const selection = ref<PolicySelection | null>(null);
const file = ref<File | null>(null);
const loading = ref(false);
const uploading = ref(false);
const preparing = ref(false);
const error = ref("");
let version = 0;
async function load() {
  const current = ++version;
  loading.value = true;
  error.value = "";
  try {
    const result = await fetchPolicy(props.conversationId);
    if (current === version) selection.value = result;
  } catch {
    if (current === version) error.value = t("policy.loadFailed");
  } finally {
    if (current === version) loading.value = false;
  }
}
function choose(event: Event) {
  file.value = (event.target as HTMLInputElement).files?.[0] ?? null;
  error.value = "";
}
async function upload() {
  if (!file.value || props.busy || !props.canUpload || uploading.value) return;
  if (selection.value && file.value.size > selection.value.max_upload_bytes) {
    error.value = t("policy.tooLarge");
    return;
  }
  const current = version;
  uploading.value = true;
  emit("busy", true);
  error.value = "";
  try {
    const result = await uploadPolicy(props.conversationId, file.value);
    if (current === version) { selection.value = result; file.value = null; emit("changed", props.conversationId); }
  } catch (e) {
    if (current === version) {
      const message = (e as Error).message;
      error.value = t(message.startsWith("413 ") ? "policy.tooLarge" : message.startsWith("415 ") ? "policy.pdfRequired" : message.startsWith("422 ") ? "policy.invalid" : message.startsWith("409 ") ? "policy.conflict" : "policy.failed");
    }
  } finally {
    if (current === version) { uploading.value = false; emit("busy", false); }
  }
}
function preparationError(code: string | null): string {
  const key = code === "encrypted_pdf" ? "policy.prepareEncrypted"
    : ["unreadable_pdf", "unreadable_page", "no_readable_text"].includes(code || "") ? "policy.prepareUnreadable"
    : ["unsupported_page_count", "text_too_large"].includes(code || "") ? "policy.prepareLimit"
    : code === "processing_timeout" ? "policy.prepareTimeout" : "policy.prepareFailed";
  return t(key);
}
async function prepare() {
  if (!selection.value?.document || props.busy || uploading.value || preparing.value) return;
  const current = version;
  preparing.value = true;
  emit("busy", true);
  error.value = "";
  try {
    const result = await preparePolicy(props.conversationId);
    if (current === version) { selection.value = result; emit("changed", props.conversationId); }
  } catch (e) {
    if (current === version) error.value = t((e as Error).message.startsWith("409 ") ? "policy.processingElsewhere" : "policy.prepareFailed");
  } finally {
    if (current === version) { preparing.value = false; emit("busy", false); }
  }
}

watch(() => props.conversationId, () => { selection.value = null; file.value = null; load(); }, { immediate: true });
onUnmounted(() => { version++; emit("busy", false); });
</script>

<template>
  <section class="panel policy-upload" aria-labelledby="policy-heading" data-testid="policy-upload">
    <h2 id="policy-heading">{{ t("policy.title") }}</h2>
    <p data-testid="policy-source">{{ selection?.document ? t("policy.selected", { name: selection.document.filename }) : t("policy.demo") }}</p>
    <p>{{ t("policy.sample") }}</p>
    <p v-if="loading" role="status">{{ t("policy.loading") }}</p>
    <template v-else-if="selection?.document">
      <p data-testid="policy-filename">{{ selection.document.filename }}</p>
      <p role="status" data-testid="policy-status">{{ t(`policy.status.${preparing ? 'processing' : selection.document.status}`) }}</p>
      <p>{{ t(selection.document.status === 'ready' ? "policy.usedForNew" : "policy.noAnswersYet") }}</p>
      <p v-if="selection.document.status === 'ready'" data-testid="policy-counts">{{ t("policy.preparedCounts", { pages: selection.document.page_count || 0, passages: selection.document.passage_count || 0 }) }}</p>
      <p v-if="selection.document.status === 'failed' && !preparing" role="alert">{{ preparationError(selection.document.error) }}</p>
      <button v-if="selection.document.status !== 'ready'" class="btn" data-testid="prepare-policy" :disabled="busy || preparing || uploading" @click="prepare">{{ t(selection.document.status === 'processing' ? "policy.checkPreparation" : selection.document.status === 'failed' ? "policy.retryPreparation" : "policy.prepare") }}</button>
    </template>
    <form v-else-if="selection && canUpload" @submit.prevent="upload">
      <label for="policy-file">{{ t("policy.choose") }}</label>
      <input id="policy-file" type="file" accept="application/pdf,.pdf" :disabled="busy || uploading" @change="choose" />
      <p>{{ t("policy.limit", { mb: Math.round(selection.max_upload_bytes / 1024 / 1024) }) }}</p>
      <button class="btn" :disabled="busy || uploading || !file" data-testid="upload-policy">{{ t("policy.upload") }}</button>
    </form>
    <p v-else-if="selection">{{ t("policy.locked") }}</p>
    <p v-if="uploading" role="status">{{ t("policy.uploading") }}</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <button v-if="error && !selection" class="btn" :disabled="loading" @click="load">{{ t("chat.retry") }}</button>
  </section>
</template>
