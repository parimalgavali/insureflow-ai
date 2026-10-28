<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type { Citation, ClaimCard, ClaimFacts, ClaimStatus, RiskSignal } from "../api/client";
import CitationPill from "./CitationPill.vue";
import { t } from "../i18n";

const props = defineProps<{
  facts: ClaimFacts | null;
  missing: string[];
  citations: Citation[];
  risk: RiskSignal | null;
  card: ClaimCard | null;
  status: ClaimStatus;
  busy: boolean;
}>();
const emit = defineEmits<{ review: [patch: Record<string, unknown>] }>();

const FACT_KEYS = [
  "incident_date",
  "incident_time",
  "location",
  "event_type",
  "description",
  "third_party_involved",
  "third_party_known",
  "injuries",
  "police_report_filed",
  "witnesses",
  "damage_description",
  "estimated_amount_eur",
  "vehicle_drivable",
  "photos_attached",
];

const edits = reactive<Record<string, string>>({});
const editing = ref(false);
const activeCitation = ref<Citation | null>(null);
function toggleCitation(c: Citation) {
  activeCitation.value = activeCitation.value?.clause_id === c.clause_id ? null : c;
}
watch(
  () => props.card?.coverage_summary,
  () => (activeCitation.value = null),
);
watch(
  () => props.facts,
  () => Object.keys(edits).forEach((k) => delete edits[k]),
);

const factRows = computed(() =>
  FACT_KEYS.map((key) => {
    const value = props.facts ? (props.facts as unknown as Record<string, unknown>)[key] : null;
    return { key, label: t(`fact.${key}`), value, missing: props.missing.includes(key) };
  }),
);

function display(value: unknown): string {
  if (value === null || value === undefined || value === "unknown") return "—";
  if (typeof value === "boolean") return value ? t("card.yes") : t("card.no");
  return String(value);
}

/** Replace [A.2.2.2.2]-style references in the summary with citation pills. */
const summaryParts = computed(() => {
  const text = props.card?.coverage_summary ?? "";
  const byId = new Map(props.citations.map((c) => [c.clause_id, c]));
  const parts: Array<{ text: string } | { citation: Citation }> = [];
  const re = /\[([A-Z]\.\d+(?:\.\d+)*)\]/g;
  let last = 0;
  for (const m of text.matchAll(re)) {
    if (m.index! > last) parts.push({ text: text.slice(last, m.index) });
    const c = byId.get(m[1]);
    parts.push(c ? { citation: c } : { text: m[0] });
    last = m.index! + m[0].length;
  }
  if (last < text.length) parts.push({ text: text.slice(last) });
  return parts;
});

const fmt = (n: number) => Math.round(n).toLocaleString("en");
const canReview = computed(() => props.status === "awaiting_review" && !props.busy);

function submitReview() {
  const patch: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(edits)) {
    if (v === "") continue;
    const current = (props.facts as unknown as Record<string, unknown>)[k];
    if (typeof current === "boolean" || current === null) {
      const lower = v.toLowerCase();
      const yes = ["yes", "true", "ja"];
      const no = ["no", "false", "nein"];
      patch[k] = yes.includes(lower) ? true : no.includes(lower) ? false : v;
    } else if (typeof current === "number") patch[k] = Number(v);
    else patch[k] = v;
  }
  editing.value = false;
  emit("review", patch);
}
</script>

<template>
  <aside class="panel card" :aria-label="t('card.aria')">
    <h2>
      {{ t("card.title") }}
      <span class="badge" :class="status" data-testid="status">{{ t(`status.${status}`) }}</span>
    </h2>

    <section>
      <h3>{{ t("card.facts") }}</h3>
      <p v-if="!facts" class="empty">{{ t("card.factsEmpty") }}</p>
      <dl v-else class="facts">
        <template v-for="row in factRows" :key="row.key">
          <dt>{{ row.label }}</dt>
          <dd v-if="editing && status === 'awaiting_review'">
            <input v-model="edits[row.key]" :placeholder="display(row.value)" :aria-label="row.label" />
          </dd>
          <dd v-else :class="{ missing: row.missing }" :data-testid="`fact-${row.key}`">
            {{ row.missing ? t("card.missing") : display(row.value) }}
          </dd>
        </template>
      </dl>
    </section>

    <section>
      <h3>{{ t("card.coverage") }}</h3>
      <template v-if="card">
        <span class="badge" :class="card.coverage_status" data-testid="coverage">{{ t(`status.${card.coverage_status}`) }}</span>
        <p class="summary" data-testid="summary">
          <template v-for="(part, i) in summaryParts" :key="i">
            <CitationPill
              v-if="'citation' in part"
              :citation="part.citation"
              :active="activeCitation?.clause_id === part.citation.clause_id"
              @select="toggleCitation"
            />
            <template v-else>{{ part.text }}</template>
          </template>
        </p>
        <p v-if="card.citations.length" class="disclaimer">
          {{ t("card.clauses") }}
          <CitationPill
            v-for="c in card.citations"
            :key="c.clause_id"
            :citation="c"
            :active="activeCitation?.clause_id === c.clause_id"
            @select="toggleCitation"
          />
        </p>
        <blockquote v-if="activeCitation" class="clause" data-testid="popover" aria-live="polite">
          <strong>AKB 2015 {{ activeCitation.clause_id }} – {{ activeCitation.title || t("card.clause") }}</strong>
          {{ activeCitation.excerpt }}
          <small v-if="activeCitation.page">{{ t("card.page", { page: activeCitation.page }) }}</small>
        </blockquote>
      </template>
      <p v-else-if="citations.length" class="empty">{{ t("card.composing", { n: citations.length }) }}</p>
      <p v-else class="empty">{{ t("card.coverageEmpty") }}</p>
    </section>

    <section>
      <h3>{{ t("card.risk") }}</h3>
      <template v-if="risk">
        <span class="badge" :class="risk.band" data-testid="risk">{{ t(`band.${risk.band}`) }}</span>
        <ul class="reasons">
          <li v-for="r in risk.reasons" :key="r">{{ r }}</li>
        </ul>
        <p class="disclaimer">{{ t("card.riskDisclaimer") }}</p>
      </template>
      <p v-if="card?.cost" class="cost" data-testid="cost">
        {{ t("card.cost", { claim: fmt(card.cost.claim_eur), portfolio: fmt(card.cost.portfolio_claim_eur), freq: card.cost.claims_per_year.toFixed(2) }) }}
        <small>· {{ card.cost.basis }} – {{ t("card.costNote") }}</small>
      </p>
      <p v-else class="empty">{{ t("card.riskEmpty") }}</p>
    </section>

    <section v-if="card?.missing_documents.length">
      <h3>{{ t("card.provide") }}</h3>
      <ul class="docs">
        <li v-for="d in card.missing_documents" :key="d"><label><input type="checkbox" /> {{ d }}</label></li>
      </ul>
    </section>

    <section v-if="card?.next_steps.length">
      <h3>{{ t("card.nextSteps") }}</h3>
      <ol class="steps">
        <li v-for="s in card.next_steps" :key="s">{{ s }}</li>
      </ol>
    </section>

    <section class="review">
      <template v-if="status === 'reviewed'">
        <span class="badge reviewed">{{ t("card.reviewedBadge") }}</span>
        <small v-if="card?.review?.note" class="disclaimer">{{ card.review.note }}</small>
      </template>
      <template v-else>
        <button class="btn primary" :disabled="!canReview" data-testid="review" @click="submitReview">{{ t("card.sendToAdjuster") }}</button>
        <button v-if="status === 'awaiting_review'" class="btn" type="button" @click="editing = !editing">
          {{ editing ? t("card.doneEditing") : t("card.editFacts") }}
        </button>
      </template>
    </section>
  </aside>
</template>
