<script setup lang="ts">
import type { HistoryEntry } from "../api/client";
import { locale, t } from "../i18n";

defineProps<{ entries: HistoryEntry[] }>();

function actorLabel(actor: string): string {
  return t(actor === "adjuster" ? "history.reviewer" : actor === "customer" ? "history.customer" : "history.unknownActor");
}

function display(value: string | number | boolean | null): string {
  if (value === null) return "—";
  if (typeof value === "boolean") return t(value ? "card.yes" : "card.no");
  return String(value);
}
</script>

<template>
  <section class="claim-history" :aria-label="t('history.title')" data-testid="claim-history">
    <h3>{{ t("history.title") }}</h3>
    <p class="disclaimer">{{ t("history.availability") }}</p>
    <p v-if="!entries.length" class="empty">{{ t("history.empty") }}</p>
    <ol v-else>
      <li v-for="entry in entries" :key="entry.id" data-testid="history-event" :data-history-kind="entry.kind">
        <strong>{{ t(`history.kind.${entry.kind}`) }}</strong>
        <time :datetime="entry.created_at" :title="entry.created_at">{{ new Date(entry.created_at).toLocaleString(locale) }}</time>
        <p>{{ actorLabel(entry.actor) }}</p>
        <p v-if="entry.decision">{{ t("history.decision") }}: {{ t(`history.decision.${entry.decision}`) }}</p>
        <p v-if="entry.decision || entry.note" class="history-note">{{ entry.note || t("history.noNote") }}</p>
        <ul v-if="entry.changes.length">
          <li v-for="change in entry.changes" :key="change.field">{{ t(`fact.${change.field}`) }}: {{ display(change.before) }} → {{ display(change.after) }}</li>
        </ul>
      </li>
    </ol>
  </section>
</template>
