<script setup lang="ts">
import type { EvidenceAttachment } from "../api/client";
import { t } from "../i18n";
defineProps<{ attachments: EvidenceAttachment[] }>();
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
      </li>
    </ul>
  </section>
</template>
