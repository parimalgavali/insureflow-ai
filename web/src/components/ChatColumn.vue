<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import type { DocumentType } from "../api/client";
import type { ChatItem } from "../store";
import { t } from "../i18n";

const props = defineProps<{ messages: ChatItem[]; missing: string[]; busy: boolean; error: string | null; canSend: boolean; retryable?: boolean; restoredDraft?: { text: string; file: File | null; documentType: DocumentType } | null }>();
const emit = defineEmits<{ send: [text: string, file: File | null, documentType: DocumentType]; retry: [] }>();

const CHIP_KEYS = ["incident_date", "event_type", "third_party_involved", "damage_description", "police_report_filed", "location"];

const draft = ref("");
const file = ref<File | null>(null);
const documentType = ref<DocumentType>("other_document");
watch(() => props.restoredDraft, (value) => {
  if (value) { draft.value = value.text; file.value = value.file; documentType.value = value.documentType; }
});
const log = ref<HTMLElement | null>(null);
const chips = computed(() => props.missing.filter((m) => CHIP_KEYS.includes(m)).slice(0, 3).map((m) => t(`chip.${m}`)));

watch(
  () => props.messages.map((m) => m.content).join("\u0000"),
  async () => {
    await nextTick();
    log.value?.scrollTo({ top: log.value.scrollHeight });
  },
);

function send() {
  const text = draft.value.trim();
  if (!text || props.busy || !props.canSend) return;
  emit("send", text, file.value, documentType.value);
  draft.value = "";
  file.value = null;
}

function onKey(e: KeyboardEvent) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
}

function onFile(e: Event) {
  const input = e.target as HTMLInputElement;
  file.value = input.files?.[0] ?? null;
  documentType.value = file.value?.type.startsWith("image/") ? "damage_photo" : "other_document";
  input.value = "";
}
</script>

<template>
  <section class="panel chat" :aria-label="t('chat.aria')">
    <div ref="log" class="log" role="log" aria-live="polite" aria-relevant="additions text">
      <div v-for="m in messages" :key="m.id" class="bubble" :class="[m.role, { streaming: m.streaming }]">{{ m.content }}</div>
    </div>
    <div v-if="chips.length && !busy && canSend" class="chips" :aria-label="t('chat.suggested')">
      <button v-for="c in chips" :key="c" type="button" class="chip" @click="draft = c">{{ c }}</button>
    </div>
    <div v-if="error" class="error" role="alert">
      <span>{{ t("chat.error", { error }) }}</span>
      <button v-if="retryable !== false" class="btn" type="button" @click="emit('retry')">{{ t("chat.retry") }}</button>
    </div>
    <div v-if="file" class="attach">
      {{ t("chat.attached", { name: file.name }) }}
      <button class="chip" type="button" :disabled="busy" @click="file = null">{{ t("chat.remove") }}</button>
      <label for="evidence-purpose">{{ t("evidence.purpose") }}</label>
      <select id="evidence-purpose" v-model="documentType" :disabled="busy || !canSend">
        <option v-if="file.type.startsWith('image/')" value="damage_photo">{{ t("evidence.type.damage_photo") }}</option>
        <option v-for="kind in ['repair_estimate', 'police_report', 'other_document']" :key="kind" :value="kind">{{ t(`evidence.type.${kind}`) }}</option>
      </select>
    </div>
    <form class="composer" @submit.prevent="send">
      <textarea
        v-model="draft"
        rows="1"
        :disabled="busy || !canSend"
        :placeholder="canSend ? t('chat.placeholder') : t('chat.placeholderReviewed')"
        :aria-label="t('chat.yourMessage')"
        @keydown="onKey"
      />
      <div class="actions">
        <label class="btn" :title="t('chat.attachTitle')">
          📎<span class="sr-only">{{ t("chat.attachFile") }}</span>
          <input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" class="sr-only" :disabled="busy || !canSend" @change="onFile" />
        </label>
        <button class="btn primary" type="submit" :disabled="busy || !canSend || !draft.trim()">{{ busy ? "…" : t("chat.send") }}</button>
      </div>
    </form>
  </section>
</template>
