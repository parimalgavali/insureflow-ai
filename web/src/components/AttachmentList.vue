<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import type { ClaimFacts, EvidenceAttachment, EvidenceDecision, EvidenceSuggestion } from "../api/client";
import { t } from "../i18n";
import { evidenceReadProblem } from "../evidenceMessages";
const props = defineProps<{ attachments: EvidenceAttachment[]; facts?: ClaimFacts | null; busy?: boolean; canExtract?: boolean; canConfirm?: boolean; canReplace?: boolean; canManual?: boolean }>();
const emit = defineEmits<{ extract: [attachmentId: string]; decide: [suggestionId: string, decision: EvidenceDecision]; replaceFile: [attachmentId: string, file: File]; manualEntry: [] }>();
const display = (value: string | number | boolean | null) => value === null || value === "unknown" ? "—" : typeof value === "boolean" ? t(value ? "card.yes" : "card.no") : String(value);
const replace = reactive<Record<string, boolean>>({});
watch(() => props.facts, () => Object.keys(replace).forEach((key) => delete replace[key]));
const current = (suggestion: EvidenceSuggestion) => props.facts?.[suggestion.field] ?? null;
const conflict = (suggestion: EvidenceSuggestion) => current(suggestion) !== null && current(suggestion) !== "unknown" && current(suggestion) !== suggestion.value;
function decide(suggestion: EvidenceSuggestion, decision: "accept" | "reject") {
  if (props.busy || !props.canConfirm || (decision === "accept" && conflict(suggestion) && !replace[suggestion.id])) return;
  emit("decide", suggestion.id, { decision, expected_current: current(suggestion), replace_existing: !!replace[suggestion.id] });
}
const replacing = ref<string | null>(null);
const chosenCopy = ref<File | null>(null);
watch(() => props.attachments, (attachments) => {
  if (replacing.value && !attachments.some((a) => a.id === replacing.value && a.is_current !== false)) {
    replacing.value = null; chosenCopy.value = null;
  }
});
function beginReplacement(id: string) { replacing.value = id; chosenCopy.value = null; }
function chooseCopy(event: Event) {
  const input = event.target as HTMLInputElement;
  chosenCopy.value = input.files?.[0] ?? null;
  input.value = "";
}
function saveCopy() {
  if (!props.busy && props.canReplace && replacing.value && chosenCopy.value) emit("replaceFile", replacing.value, chosenCopy.value);
}
const formats: Record<string, string> = { "application/pdf": "PDF", "image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WebP" };
</script>

<template>
  <section class="evidence-list" data-testid="evidence-list">
    <h3>{{ t("evidence.title") }}</h3>
    <p v-if="!attachments.length">{{ t("evidence.empty") }}</p>
    <ul v-else>
      <li v-for="attachment in attachments" :key="attachment.id" :data-testid="`attachment-${attachment.id}`">
        <strong>{{ attachment.filename }}</strong>
        <p>{{ t("evidence.copyVersion", { n: attachment.revision || 1 }) }} · {{ t(attachment.is_current === false ? "evidence.previousCopy" : "evidence.currentCopy") }}</p>
        <p>{{ t(`evidence.type.${attachment.document_type}`) }} · {{ attachment.media_type === 'unknown' ? t('evidence.type.unknown') : formats[attachment.content_type] || t('evidence.type.unknown') }}</p>
        <p>{{ t(`evidence.state.${attachment.processing_state}`) }}</p>
        <p v-if="attachment.processing_state === 'failed'" role="status">{{ evidenceReadProblem(attachment.error) }}</p>
        <button v-if="canExtract && attachment.is_current !== false && attachment.media_type === 'pdf' && attachment.processing_state !== 'ready'" class="btn" type="button" :disabled="busy" :data-testid="`extract-evidence-${attachment.id}`" @click="emit('extract', attachment.id)">{{ t(attachment.processing_state === 'stored' ? 'evidence.read' : 'evidence.retryRead') }}</button>
        <template v-if="attachment.is_current !== false">
          <template v-if="attachment.processing_state === 'failed'">
            <p>{{ t("evidence.manualHint") }}</p>
            <button v-if="canManual" class="btn" type="button" :disabled="busy" @click="emit('manualEntry')">{{ t("evidence.enterManually") }}</button>
          </template>
          <button v-if="canReplace && attachment.content_type === 'application/pdf' && replacing !== attachment.id" class="btn" type="button" :disabled="busy" @click="beginReplacement(attachment.id)">{{ t("evidence.replaceCopy") }}</button>
          <form v-if="canReplace && replacing === attachment.id" @submit.prevent="saveCopy">
            <label :for="`evidence-copy-${attachment.id}`">{{ t("evidence.chooseCopy") }}</label>
            <input :id="`evidence-copy-${attachment.id}`" type="file" accept="application/pdf" :disabled="busy" @change="chooseCopy" />
            <p v-if="chosenCopy">{{ t("evidence.confirmCopy", { old: attachment.filename, next: chosenCopy.name }) }}</p>
            <button class="btn" type="submit" :disabled="busy || !chosenCopy">{{ t("evidence.saveCopy") }}</button>
            <button class="btn" type="button" :disabled="busy" @click="replacing = null; chosenCopy = null">{{ t("card.cancelEdits") }}</button>
          </form>
        </template>
        <template v-if="attachment.processing_state === 'ready'">
          <p v-if="!attachment.suggestions?.length">{{ t("evidence.noSuggestions") }}</p>
          <template v-else>
            <h4>{{ t("evidence.suggestions") }}</h4>
            <p>{{ t("evidence.notConfirmed") }}</p>
            <ul>
              <li v-for="suggestion in attachment.suggestions" :key="suggestion.id" data-testid="evidence-suggestion">
                <strong>{{ t(`fact.${suggestion.field}`) }}</strong>
                <p>{{ t("evidence.current") }}: {{ display(current(suggestion)) }}</p>
                <p>{{ t("evidence.suggested") }}: {{ display(suggestion.value) }}</p>
                <p v-if="conflict(suggestion) && suggestion.status === 'pending'" class="assessment-warning">{{ t("evidence.conflict") }}</p>
                <p>{{ t(`evidence.decision.${suggestion.status}`) }}</p>
                <p>{{ suggestion.source_name }} · {{ t("card.page", { page: suggestion.page }) }}</p>
                <blockquote>{{ suggestion.quote }}</blockquote>
                <template v-if="canConfirm && attachment.is_current !== false && suggestion.status === 'pending'">
                  <label v-if="conflict(suggestion)"><input v-model="replace[suggestion.id]" type="checkbox" :disabled="busy" /> {{ t("evidence.replaceValue") }}</label>
                  <button class="btn" type="button" :disabled="busy || (conflict(suggestion) && !replace[suggestion.id])" @click="decide(suggestion, 'accept')">{{ t("evidence.accept") }}</button>
                  <button class="btn" type="button" :disabled="busy" @click="decide(suggestion, 'reject')">{{ t("evidence.reject") }}</button>
                </template>
              </li>
            </ul>
          </template>
        </template>
      </li>
    </ul>
  </section>
</template>
