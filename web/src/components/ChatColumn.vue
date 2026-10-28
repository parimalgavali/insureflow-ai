<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import type { ChatItem } from "../store";

const props = defineProps<{ messages: ChatItem[]; missing: string[]; busy: boolean; error: string | null; canSend: boolean }>();
const emit = defineEmits<{ send: [text: string, file: File | null]; retry: [] }>();

const CHIPS: Record<string, string> = {
  incident_date: "It happened on …",
  event_type: "Someone hit my parked car and left",
  third_party_involved: "No other vehicle or person was involved",
  damage_description: "The rear bumper is dented",
  police_report_filed: "The police were not informed",
  location: "It happened in …",
};

const draft = ref("");
const file = ref<File | null>(null);
const log = ref<HTMLElement | null>(null);
const chips = computed(() => props.missing.map((m) => CHIPS[m]).filter(Boolean).slice(0, 3));

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
  <section class="panel chat" aria-label="Conversation">
    <div ref="log" class="log" role="log" aria-live="polite" aria-relevant="additions text">
      <div v-for="m in messages" :key="m.id" class="bubble" :class="[m.role, { streaming: m.streaming }]">{{ m.content }}</div>
    </div>
    <div v-if="chips.length && !busy && canSend" class="chips" aria-label="Suggested answers">
      <button v-for="c in chips" :key="c" type="button" class="chip" @click="draft = c">{{ c }}</button>
    </div>
    <div v-if="error" class="error" role="alert">
      <span>Something went wrong: {{ error }}</span>
      <button class="btn" type="button" @click="emit('retry')">Retry</button>
    </div>
    <div v-if="file" class="attach">Attached: {{ file.name }} <button class="chip" type="button" @click="file = null">remove</button></div>
    <form class="composer" @submit.prevent="send">
      <textarea
        v-model="draft"
        rows="1"
        :disabled="busy || !canSend"
        :placeholder="canSend ? 'Describe what happened to your car…' : 'This claim has been reviewed.'"
        aria-label="Your message"
        @keydown="onKey"
      />
      <div class="actions">
        <label class="btn" title="Attach a photo or PDF">
          📎<span class="sr-only">Attach file</span>
          <input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" class="sr-only" :disabled="busy || !canSend" @change="onFile" />
        </label>
        <button class="btn primary" type="submit" :disabled="busy || !canSend || !draft.trim()">{{ busy ? "…" : "Send" }}</button>
      </div>
    </form>
  </section>
</template>
