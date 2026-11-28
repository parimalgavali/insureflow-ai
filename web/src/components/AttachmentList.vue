<script setup lang="ts">
import type { EvidenceAttachment } from "../api/client";
import { t } from "../i18n";
defineProps<{ attachments: EvidenceAttachment[]; busy?: boolean; canExtract?: boolean }>();
const emit = defineEmits<{ extract: [attachmentId: string] }>();
const display = (value: string | number | boolean) => typeof value === "boolean" ? t(value ? "card.yes" : "card.no") : String(value);
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
                <strong>{{ t(`fact.${suggestion.field}`) }}: {{ display(suggestion.value) }}</strong>
                <p>{{ suggestion.source_name }} · {{ t("card.page", { page: suggestion.page }) }}</p>
                <blockquote>{{ suggestion.quote }}</blockquote>
              </li>
            </ul>
          </template>
        </template>
      </li>
    </ul>
  </section>
</template>
