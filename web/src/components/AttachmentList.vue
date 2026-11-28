<script setup lang="ts">
import { reactive, watch } from "vue";
import type { ClaimFacts, EvidenceAttachment, EvidenceDecision, EvidenceSuggestion } from "../api/client";
import { t } from "../i18n";
const props = defineProps<{ attachments: EvidenceAttachment[]; facts?: ClaimFacts | null; busy?: boolean; canExtract?: boolean; canConfirm?: boolean }>();
const emit = defineEmits<{ extract: [attachmentId: string]; decide: [suggestionId: string, decision: EvidenceDecision] }>();
const display = (value: string | number | boolean | null) => value === null || value === "unknown" ? "—" : typeof value === "boolean" ? t(value ? "card.yes" : "card.no") : String(value);
const replace = reactive<Record<string, boolean>>({});
watch(() => props.facts, () => Object.keys(replace).forEach((key) => delete replace[key]));
const current = (suggestion: EvidenceSuggestion) => props.facts?.[suggestion.field] ?? null;
const conflict = (suggestion: EvidenceSuggestion) => current(suggestion) !== null && current(suggestion) !== "unknown" && current(suggestion) !== suggestion.value;
function decide(suggestion: EvidenceSuggestion, decision: "accept" | "reject") {
  if (props.busy || !props.canConfirm || (decision === "accept" && conflict(suggestion) && !replace[suggestion.id])) return;
  emit("decide", suggestion.id, { decision, expected_current: current(suggestion), replace_existing: !!replace[suggestion.id] });
}
function errorText(code: string | null) {
  if (["no_readable_text", "unreadable_page", "unreadable_pdf", "encrypted_pdf"].includes(code || "")) return t("evidence.readUnreadable");
  if (code === "document_text_too_long") return t("evidence.readTooLong");
  return t("evidence.readFailed");
}
const formats: Record<string, string> = { "application/pdf": "PDF", "image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WebP" };
</script>

<template>
  <section class="evidence-list" data-testid="evidence-list">
    <h3>{{ t("evidence.title") }}</h3>
    <p v-if="!attachments.length">{{ t("evidence.empty") }}</p>
    <ul v-else>
      <li v-for="attachment in attachments" :key="attachment.id">
        <strong>{{ attachment.filename }}</strong>
        <p>{{ t(`evidence.type.${attachment.document_type}`) }} · {{ attachment.media_type === 'unknown' ? t('evidence.type.unknown') : formats[attachment.content_type] || t('evidence.type.unknown') }}</p>
        <p>{{ t(`evidence.state.${attachment.processing_state}`) }}</p>
        <p v-if="attachment.processing_state === 'failed'" role="status">{{ errorText(attachment.error) }}</p>
        <button v-if="canExtract && attachment.media_type === 'pdf' && attachment.processing_state !== 'ready'" class="btn" type="button" :disabled="busy" :data-testid="`extract-evidence-${attachment.id}`" @click="emit('extract', attachment.id)">{{ t(attachment.processing_state === 'stored' ? 'evidence.read' : 'evidence.retryRead') }}</button>
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
                <template v-if="canConfirm && suggestion.status === 'pending'">
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
