<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import type { ChatItem } from "../store";
import { t } from "../i18n";

const props = defineProps<{ messages: ChatItem[]; missing: string[]; busy: boolean; error: string | null; canSend: boolean }>();
const emit = defineEmits<{ send: [text: string, file: File | null]; retry: [] }>();

const CHIP_KEYS = ["incident_date", "event_type", "third_party_involved", "damage_description", "police_report_filed", "location"];

const draft = ref("");
const file = ref<File | null>(null);
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
  emit("send", text, file.value);
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
  file.value = (e.target as HTMLInputElement).files?.[0] ?? null;
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
      <button class="btn" type="button" @click="emit('retry')">{{ t("chat.retry") }}</button>
    </div>
    <div v-if="file" class="attach">{{ t("chat.attached", { name: file.name }) }} <button class="chip" type="button" @click="file = null">{{ t("chat.remove") }}</button></div>
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
