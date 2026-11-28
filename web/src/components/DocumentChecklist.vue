<script setup lang="ts">
import { reactive } from "vue";
import type { DocumentChecklistItem, EvidenceAttachment } from "../api/client";
import { t } from "../i18n";
const props = defineProps<{ items: DocumentChecklistItem[]; attachments: EvidenceAttachment[]; busy: boolean; editable: boolean; reviewer: boolean; canConfirm: boolean }>();
const emit = defineEmits<{ link: [itemId: string, attachmentId: string, linked: boolean]; confirm: [itemId: string, attachmentIds: string[], confirmed: boolean] }>();
const selection = reactive<Record<string, string>>({});
const file = (id: string) => props.attachments.find((attachment) => attachment.id === id);
const choices = (item: DocumentChecklistItem) => props.attachments.filter((attachment) => attachment.is_current !== false && ["image", "pdf"].includes(attachment.media_type) && (item.document_type !== "damage_photo" || attachment.media_type === "image") && (!item.document_type || attachment.document_type === item.document_type || (item.document_type !== "damage_photo" && attachment.document_type === "other_document")) && !item.attachment_ids.includes(attachment.id));
function link(item: DocumentChecklistItem) {
  const attachmentId = selection[item.id];
  if (!props.busy && attachmentId) emit("link", item.id, attachmentId, true);
}
</script>

<template>
  <section data-testid="document-checklist">
    <h3>{{ t("checklist.title") }}</h3>
    <p>{{ t("checklist.explanation") }}</p>
    <p v-if="!items.length">{{ t("checklist.empty") }}</p>
    <ul v-else>
      <li v-for="item in items" :key="item.id" :data-testid="`document-item-${item.id}`">
        <strong>{{ item.label }}</strong>
        <p>{{ t(`checklist.origin.${item.origin}`) }} · <span :data-testid="`document-state-${item.id}`">{{ t(`checklist.state.${item.status}`) }}</span></p>
        <ul v-if="item.attachment_ids.length">
          <li v-for="id in item.attachment_ids" :key="id">
            {{ file(id)?.filename || t("checklist.fileUnavailable") }} · {{ t("evidence.copyVersion", { n: file(id)?.revision || 1 }) }}
            <span v-if="file(id)?.processing_state === 'failed'"> · {{ t("evidence.state.failed") }}</span>
            <button v-if="editable && !reviewer" class="btn" :disabled="busy" @click="emit('link', item.id, id, false)">{{ t("checklist.unlink") }}</button>
          </li>
        </ul>
        <form v-if="editable && !reviewer && choices(item).length" @submit.prevent="link(item)">
          <label :for="`checklist-file-${item.id}`">{{ t("checklist.chooseFile") }}</label>
          <select :id="`checklist-file-${item.id}`" v-model="selection[item.id]" :disabled="busy">
            <option value="">{{ t("checklist.choosePlaceholder") }}</option>
            <option v-for="attachment in choices(item)" :key="attachment.id" :value="attachment.id">{{ attachment.filename }}</option>
          </select>
          <button class="btn" :disabled="busy || !selection[item.id]">{{ t("checklist.link") }}</button>
        </form>
        <template v-if="reviewer && canConfirm">
          <button v-if="item.attachment_ids.length && item.status !== 'confirmed'" class="btn" :disabled="busy" @click="emit('confirm', item.id, [...item.attachment_ids], true)">{{ t("checklist.confirm") }}</button>
          <button v-if="item.status === 'confirmed'" class="btn" :disabled="busy" @click="emit('confirm', item.id, [...item.attachment_ids], false)">{{ t("checklist.clearConfirmation") }}</button>
        </template>
      </li>
    </ul>
  </section>
</template>
