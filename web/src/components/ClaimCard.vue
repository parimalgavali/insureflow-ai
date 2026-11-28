<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import type { Citation, ClaimCard, ClaimFacts, ClaimStatus, RiskSignal, RiskStatus, HistoryEntry, EvidenceAttachment } from "../api/client";
import CitationPill from "./CitationPill.vue";
import AttachmentList from "./AttachmentList.vue";
import ClaimHistory from "./ClaimHistory.vue";
import { t } from "../i18n";

const props = defineProps<{
  facts: ClaimFacts | null;
  missing: string[];
  citations: Citation[];
  risk: RiskSignal | null;
  riskStatus?: RiskStatus;
  riskMissing?: string[];
  card: ClaimCard | null;
  status: ClaimStatus;
  busy: boolean;
  reviewer?: boolean;
  history?: HistoryEntry[];
  attachments?: EvidenceAttachment[];
  claimId?: string | null;
}>();
const emit = defineEmits<{ submit: []; review: [patch: Record<string, unknown>, note?: string]; requestInfo: [note: string]; reassess: []; customerCorrect: [patch: Record<string, unknown>]; customerRefresh: [] }>();
const requestNote = ref("");
const reviewNote = ref("");

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
  () => { Object.keys(edits).forEach((k) => delete edits[k]); editing.value = false; reviewNote.value = ""; },
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

const coverageUncertainty = computed(() => props.missing.length ? "missing_facts" : props.card?.assessment_stale ? "human_review" : props.card?.coverage_uncertainty ?? (props.card?.coverage_status === "no_evidence" ? "missing_policy_wording" : props.card?.coverage_status === "unclear" ? "human_review" : null));
const uploadedCoverage = computed(() => (props.card?.coverage_source ?? props.citations[0]?.source) === "uploaded_policy");
const coveragePolicyName = computed(() => props.card?.coverage_policy_name ?? props.citations[0]?.source_name ?? "");
const riskAvailability = computed(() => props.riskStatus ?? props.card?.risk_status ?? (props.risk ? "available" : "pending"));
const visibleRisk = computed(() => riskAvailability.value === "available" ? props.risk : null);
const riskNeeded = computed(() => props.riskMissing ?? props.card?.risk_missing ?? []);
const riskInputLabel = (key: string) => t(key.startsWith("policy_") ? `risk.${key}` : `fact.${key}`);

const fmt = (n: number) => Math.round(n).toLocaleString("en");
const canReview = computed(() => props.reviewer && props.status === "awaiting_review" && !props.busy);
const canEdit = computed(() => !!props.facts && (props.reviewer ? props.status === "awaiting_review" : ["collecting", "assessed", "information_needed"].includes(props.status)));
const eventOptions = ["unknown", "collision", "hit_and_run", "theft", "vandalism", "glass", "wild_animal", "storm_hail", "fire", "other"];

const booleanFields = new Set(["third_party_involved", "third_party_known", "injuries", "police_report_filed", "witnesses", "vehicle_drivable", "photos_attached"]);
const draftPatch = computed(() => {
  const patch: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(edits)) {
    const current = (props.facts as unknown as Record<string, unknown>)?.[k];
    const text = v.trim();
    let value: unknown = text || null;
    if (text && booleanFields.has(k)) {
      const lower = text.toLowerCase();
      value = ["yes", "true", "ja"].includes(lower) ? true : ["no", "false", "nein"].includes(lower) ? false : text;
    } else if (text && k === "estimated_amount_eur") {
      value = Number.isFinite(Number(text)) ? Number(text) : text;
    }
    if (value !== current) patch[k] = value;
  }
  return patch;
});

const draftErrors = computed(() => {
  const errors: Record<string, string> = {};
  if (props.reviewer) return errors;
  const day = draftPatch.value.incident_date;
  if (day !== undefined && day !== null) {
    const date = typeof day === "string" && /^\d{4}-\d{2}-\d{2}$/.test(day) ? new Date(`${day}T00:00:00Z`) : new Date(NaN);
    if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== day) errors.incident_date = t("customer.invalidDate");
  }
  const time = draftPatch.value.incident_time;
  if (time !== undefined && time !== null && (typeof time !== "string" || !/^([01]\d|2[0-3]):[0-5]\d$/.test(time))) errors.incident_time = t("customer.invalidTime");
  const amount = draftPatch.value.estimated_amount_eur;
  if (amount !== undefined && amount !== null && (typeof amount !== "number" || amount < 0)) errors.estimated_amount_eur = t("customer.invalidAmount");
  return errors;
});

function saveCustomerCorrections() {
  if (!props.busy && Object.keys(draftPatch.value).length && !Object.keys(draftErrors.value).length) emit("customerCorrect", draftPatch.value);
}

function toggleEditing() {
  Object.keys(edits).forEach((k) => delete edits[k]);
  if (!editing.value) {
    for (const key of FACT_KEYS) {
      const value = (props.facts as unknown as Record<string, unknown>)?.[key];
      edits[key] = value === null || value === undefined ? "" : String(value);
    }
  }
  editing.value = !editing.value;
}

function submitReview() {
  if (!canReview.value) return;
  if (editing.value) {
    if (Object.keys(draftPatch.value).length) {
      if (reviewNote.value.trim()) emit("review", draftPatch.value, reviewNote.value.trim());
      else emit("review", draftPatch.value);
    }
  } else if (!props.card?.assessment_stale) {
    if (reviewNote.value.trim()) emit("review", {}, reviewNote.value.trim());
    else emit("review", {});
  }
}
</script>

<template>
  <aside class="panel card" :aria-label="t('card.aria')">
    <h2>
      {{ t("card.title") }}
      <span class="badge" :class="status" data-testid="status">{{ status === 'assessed' && card?.assessment_stale ? t('customer.needsRefresh') : t(`status.${status}`) }}</span>
    </h2>

    <section v-if="card?.assessment_stale" class="assessment-warning" role="alert" data-testid="assessment-stale">
      <strong>{{ t("card.outOfDate") }}</strong>
      <p>{{ card.assessment_error || t("card.refreshRequired") }}</p>
      <button v-if="reviewer" class="btn" :disabled="busy" data-testid="reassess" @click="emit('reassess')">{{ t("card.retryAssessment") }}</button>
      <button v-else-if="status === 'assessed' && !missing.length && !editing" class="btn" :disabled="busy" data-testid="customer-refresh" @click="emit('customerRefresh')">{{ t("card.retryAssessment") }}</button>
    </section>

    <section>
      <h3>{{ t("card.facts") }}</h3>
      <p v-if="missing.length" class="missing-summary" data-testid="missing-summary">{{ t("customer.stillMissing") }}: {{ missing.map((key) => t(`fact.${key}`)).join(", ") }}</p>
      <p v-if="!facts" class="empty">{{ t("card.factsEmpty") }}</p>
      <dl v-else class="facts">
        <template v-for="row in factRows" :key="row.key">
          <dt>{{ row.label }}</dt>
          <dd v-if="editing && canEdit">
            <select v-if="!reviewer && booleanFields.has(row.key)" v-model="edits[row.key]" :aria-label="row.label" :disabled="busy">
              <option v-if="row.key !== 'photos_attached'" value="">{{ t("customer.notKnown") }}</option>
              <option value="true">{{ t("card.yes") }}</option><option value="false">{{ t("card.no") }}</option>
            </select>
            <select v-else-if="!reviewer && row.key === 'event_type'" v-model="edits[row.key]" :aria-label="row.label" :disabled="busy">
              <option v-for="event in eventOptions" :key="event" :value="event">{{ t(`customer.event.${event}`) }}</option>
            </select>
            <input v-else v-model="edits[row.key]" :placeholder="display(row.value)" :aria-label="row.label" :disabled="busy" :aria-invalid="!!draftErrors[row.key]" :aria-describedby="draftErrors[row.key] ? `error-${row.key}` : undefined" />
            <p v-if="draftErrors[row.key]" :id="`error-${row.key}`" class="field-error" role="alert">{{ draftErrors[row.key] }}</p>
          </dd>
          <dd v-else :class="{ missing: row.missing }" :data-testid="`fact-${row.key}`">
            {{ row.missing ? t("card.missing") : display(row.value) }}
          </dd>
        </template>
      </dl>
    </section>

    <section>
      <h3>{{ t(uploadedCoverage ? "card.policyCoverage" : "card.coverage") }}</h3>
      <p v-if="uploadedCoverage" data-testid="coverage-source">{{ t("policy.selected", { name: coveragePolicyName }) }}</p>
      <div v-if="coverageUncertainty" data-testid="coverage-uncertainty" role="status">
        <p>{{ t(`uncertainty.${coverageUncertainty}`) }}</p>
        <p>{{ t(`uncertainty.next.${coverageUncertainty}`) }}</p>
      </div>
      <p v-if="card?.coverage_summary" class="disclaimer">{{ t(uploadedCoverage ? "uncertainty.policyPreliminary" : "uncertainty.preliminary") }}</p>
      <template v-if="card && (status !== 'collecting' || card.coverage_summary)">
        <span class="badge" :class="card.assessment_stale ? 'unclear' : card.coverage_status" data-testid="coverage">{{ card.assessment_stale ? t("card.outOfDate") : t(`status.${card.coverage_status}`) }}</span>
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
          <strong>{{ activeCitation.source_name || "AKB 2015" }} {{ activeCitation.clause_id }} – {{ activeCitation.title || t("card.clause") }}</strong>
          {{ activeCitation.excerpt }}
          <small v-if="activeCitation.page">{{ t("card.page", { page: activeCitation.page }) }}</small>
        </blockquote>
      </template>
      <p v-else-if="citations.length" class="empty">{{ t("card.composing", { n: citations.length }) }}</p>
      <p v-else class="empty">{{ t("card.coverageEmpty") }}</p>
    </section>

    <section>
      <h3>{{ t("card.risk") }}</h3>
      <template v-if="visibleRisk">
        <span class="badge" :class="card?.assessment_stale ? 'unclear' : visibleRisk.band" data-testid="risk">{{ card?.assessment_stale ? t("card.outOfDate") : t(`band.${visibleRisk.band}`) }}</span>
        <ul class="reasons">
          <li v-for="r in visibleRisk.reasons" :key="r">{{ r }}</li>
        </ul>
      </template>
      <template v-else-if="riskAvailability === 'insufficient_information'">
        <span class="badge unclear" data-testid="risk-insufficient">{{ t("risk.insufficient") }}</span>
        <p>{{ t("risk.needed") }}</p>
        <ul data-testid="risk-missing"><li v-for="key in riskNeeded" :key="key">{{ riskInputLabel(key) }}</li></ul>
      </template>
      <p v-else-if="riskAvailability === 'unavailable'" data-testid="risk-unavailable">{{ t("risk.unavailable") }}</p>
      <p v-else class="empty">{{ t("card.riskEmpty") }}</p>
      <p class="disclaimer">{{ t("card.riskDisclaimer") }}</p>
      <p v-if="card?.cost" class="cost" data-testid="cost">
        {{ t("card.cost", { claim: fmt(card.cost.claim_eur), portfolio: fmt(card.cost.portfolio_claim_eur), freq: card.cost.claims_per_year.toFixed(2) }) }}
        <small>· {{ card.cost.basis }} – {{ t("card.costNote") }}</small>
      </p>
    </section>

    <AttachmentList :attachments="attachments || []" />

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

    <section v-if="card?.corrections?.length">
      <h3>{{ t("card.savedChanges") }}</h3>
      <ul class="steps">
        <li v-for="change in card.corrections" :key="change.field" :data-testid="`correction-${change.field}`">{{ t(`fact.${change.field}`) }}: {{ display(change.before) }} → {{ display(change.after) }}</li>
      </ul>
    </section>

    <div v-if="reviewer && status === 'awaiting_review'" class="review-note">
      <label for="review-note">{{ t("history.reviewNote") }}</label>
      <input id="review-note" v-model="reviewNote" maxlength="2000" :disabled="busy" />
    </div>
    <section class="review">
      <template v-if="status === 'information_needed'">
        <strong>{{ t("card.informationNeeded") }}</strong>
        <p data-testid="information-request">{{ card?.review?.note }}</p>
        <p v-if="!reviewer">{{ t("card.replyInstructions") }}</p>
      </template>
      <template v-if="status === 'reviewed'">
        <span class="badge reviewed">{{ t("card.reviewedBadge") }}</span>
        <small v-if="card?.review?.note" class="disclaimer">{{ card.review.note }}</small>
      </template>
      <template v-else>
        <template v-if="status === 'assessed'">
          <p v-if="!card?.assessment_stale">{{ t("card.readyToSubmit") }}</p>
          <button class="btn primary" :disabled="busy || editing || card?.assessment_stale" data-testid="submit" @click="emit('submit')">{{ t("card.sendToAdjuster") }}</button>
        </template>
        <p v-if="status === 'awaiting_review'">{{ t("card.submitted") }}</p>
        <button v-if="reviewer && status === 'awaiting_review'" class="btn primary" :disabled="!canReview || (editing ? !Object.keys(draftPatch).length : card?.assessment_stale)" data-testid="review" @click="submitReview">{{ editing ? t("card.saveCorrections") : t("card.recordReview") }}</button>
        <button v-if="reviewer && status === 'awaiting_review'" class="btn" type="button" :disabled="busy" @click="toggleEditing">
          {{ editing ? t("card.cancelEdits") : t("card.editFacts") }}
        </button>
      </template>
      <template v-if="!reviewer && canEdit">
        <button v-if="editing" class="btn primary" data-testid="save-customer-facts" :disabled="busy || !Object.keys(draftPatch).length || !!Object.keys(draftErrors).length" @click="saveCustomerCorrections">{{ t("card.saveCorrections") }}</button>
        <button class="btn" :disabled="busy" data-testid="edit-customer-facts" @click="toggleEditing">{{ editing ? t("card.cancelEdits") : t("card.editFacts") }}</button>
      </template>
    </section>
    <form v-if="reviewer && !editing && status === 'awaiting_review'" class="request-info" @submit.prevent="emit('requestInfo', requestNote.trim())">
      <label for="information-request-note">{{ t("card.requestDetails") }}</label>
      <textarea id="information-request-note" v-model="requestNote" maxlength="2000" :disabled="busy" required />
      <button class="btn" data-testid="request-info" :disabled="busy || !requestNote.trim()">{{ t("card.requestInfo") }}</button>
    </form>
    <template v-if="claimId">
      <ClaimHistory :entries="history || []" />
      <a :href="`#history/${claimId}`" data-testid="saved-history-link">{{ t("history.openSaved") }}</a>
    </template>
  </aside>
</template>
