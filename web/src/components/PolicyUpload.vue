<script setup lang="ts">
import { onUnmounted, ref, watch } from "vue";
import { fetchPolicy, uploadPolicy, type PolicySelection } from "../api/client";
import { t } from "../i18n";

const props = defineProps<{ conversationId: string; busy: boolean; canUpload: boolean }>();
const emit = defineEmits<{ busy: [value: boolean] }>();
const selection = ref<PolicySelection | null>(null);
const file = ref<File | null>(null);
const loading = ref(false);
const uploading = ref(false);
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
    if (current === version) { selection.value = result; file.value = null; }
  } catch (e) {
    if (current === version) {
      const message = (e as Error).message;
      error.value = t(message.startsWith("413 ") ? "policy.tooLarge" : message.startsWith("415 ") ? "policy.pdfRequired" : message.startsWith("422 ") ? "policy.invalid" : message.startsWith("409 ") ? "policy.conflict" : "policy.failed");
    }
  } finally {
    if (current === version) { uploading.value = false; emit("busy", false); }
  }
}
watch(() => props.conversationId, () => { selection.value = null; file.value = null; load(); }, { immediate: true });
onUnmounted(() => { version++; emit("busy", false); });
</script>

<template>
  <section class="panel policy-upload" aria-labelledby="policy-heading" data-testid="policy-upload">
    <h2 id="policy-heading">{{ t("policy.title") }}</h2>
    <p data-testid="policy-source">{{ t("policy.demo") }}</p>
    <p>{{ t("policy.sample") }}</p>
    <p v-if="loading" role="status">{{ t("policy.loading") }}</p>
    <template v-else-if="selection?.document">
      <p data-testid="policy-filename">{{ selection.document.filename }}</p>
      <p role="status" data-testid="policy-status">{{ t(`policy.status.${selection.document.status}`) }}</p>
      <p>{{ t("policy.notUsed") }}</p>
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
