<script setup lang="ts">
import { onUnmounted, ref, watch } from "vue";
import { fetchPolicy, uploadPolicy, preparePolicy, replacePolicy, type PolicySelection } from "../api/client";
import { t } from "../i18n";

const props = defineProps<{ conversationId: string; busy: boolean; canUpload: boolean }>();
const emit = defineEmits<{ busy: [value: boolean]; changed: [conversationId: string] }>();
const selection = ref<PolicySelection | null>(null);
const file = ref<File | null>(null);
const loading = ref(false);
const uploading = ref(false);
const preparing = ref(false);
const error = ref("");
const info = ref("");
const replacing = ref(false);
const expectedPolicyId = ref<string | null>(null);
const reloadSelection = ref(false);
let version = 0;
async function load() {
  const current = ++version;
  loading.value = true;
  error.value = "";
  replacing.value = false;
  expectedPolicyId.value = null;
  reloadSelection.value = false;
  file.value = null;
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
function beginReplacement() {
  if (!selection.value?.document || props.busy || preparing.value || uploading.value) return;
  expectedPolicyId.value = selection.value.document.id;
  replacing.value = true;
  file.value = null;
  error.value = "";
  info.value = "";
}
function cancelReplacement() {
  replacing.value = false;
  expectedPolicyId.value = null;
  file.value = null;
  error.value = "";
}

async function upload() {
  if (!file.value || props.busy || !props.canUpload || uploading.value || preparing.value || reloadSelection.value) return;
  if (selection.value && file.value.size > selection.value.max_upload_bytes) {
    error.value = t("policy.tooLarge");
    return;
  }
  const current = version;
  uploading.value = true;
  emit("busy", true);
  error.value = "";
  try {
    const expected = expectedPolicyId.value;
    const result = replacing.value && expected ? await replacePolicy(props.conversationId, expected, file.value) : await uploadPolicy(props.conversationId, file.value);
    if (current === version) {
      info.value = expected && result.document?.id === expected ? t("policy.sameFile") : "";
      selection.value = result;
      file.value = null;
      replacing.value = false;
      expectedPolicyId.value = null;
      emit("changed", props.conversationId);
    }
  } catch (e) {
    if (current === version) {
      const message = (e as Error).message;
      if (replacing.value && message.startsWith("409 ")) reloadSelection.value = true;
      error.value = t(message.startsWith("413 ") ? "policy.tooLarge" : message.startsWith("415 ") ? "policy.pdfRequired" : message.startsWith("422 ") ? "policy.invalid" : message.startsWith("409 ") ? (replacing.value ? "policy.replacementConflict" : "policy.conflict") : "policy.failed");
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
  if (!selection.value?.document || props.busy || uploading.value || preparing.value || replacing.value) return;
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
      <p v-if="selection.document.revision" data-testid="policy-revision">{{ t("policy.revision", { revision: selection.document.revision }) }}</p>
      <p v-if="(selection.document.revision || 1) > 1 && selection.document.status !== 'ready'">{{ t("policy.replacementPending") }}</p>
      <p role="status" data-testid="policy-status">{{ t(`policy.status.${preparing ? 'processing' : selection.document.status}`) }}</p>
      <p>{{ t(selection.document.status === 'ready' ? "policy.usedForNew" : "policy.noAnswersYet") }}</p>
      <p v-if="selection.document.status === 'ready'" data-testid="policy-counts">{{ t("policy.preparedCounts", { pages: selection.document.page_count || 0, passages: selection.document.passage_count || 0 }) }}</p>
      <p v-if="selection.document.status === 'failed' && !preparing" role="alert">{{ preparationError(selection.document.error) }}</p>
      <button v-if="selection.document.status !== 'ready' && canUpload" class="btn" data-testid="prepare-policy" :disabled="busy || preparing || uploading || replacing" @click="prepare">{{ t(selection.document.status === 'processing' ? "policy.checkPreparation" : selection.document.status === 'failed' ? "policy.retryPreparation" : "policy.prepare") }}</button>
      <button v-if="canUpload && !replacing" class="btn" data-testid="replace-policy" :disabled="busy || preparing || uploading || selection.document.status === 'processing'" @click="beginReplacement">{{ t("policy.replace") }}</button>
    </template>
    <form v-if="!loading && selection && canUpload && (!selection.document || replacing)" @submit.prevent="upload">
      <label for="policy-file">{{ t("policy.choose") }}</label>
      <input id="policy-file" type="file" accept="application/pdf,.pdf" :disabled="busy || uploading" @change="choose" />
      <p>{{ t("policy.limit", { mb: Math.round(selection.max_upload_bytes / 1024 / 1024) }) }}</p>
      <p v-if="replacing && file" data-testid="replacement-confirmation">{{ t("policy.confirmText", { name: file.name, current: selection.document?.filename || '' }) }}</p>
      <button class="btn" :disabled="busy || uploading || !file || reloadSelection" data-testid="upload-policy">{{ t(replacing ? "policy.confirmReplacement" : "policy.upload") }}</button>
      <button v-if="replacing" class="btn" type="button" :disabled="uploading" @click="cancelReplacement">{{ t("policy.cancelReplacement") }}</button>
    </form>
    <p v-else-if="selection && !canUpload && !selection.document">{{ t("policy.locked") }}</p>
    <p v-if="uploading" role="status">{{ t("policy.uploading") }}</p>
    <p v-if="info" role="status">{{ info }}</p>
    <p v-if="error" role="alert">{{ error }}</p>
    <button v-if="error && (!selection || reloadSelection)" class="btn" :disabled="loading" @click="load">{{ t("chat.retry") }}</button>
  </section>
</template>
