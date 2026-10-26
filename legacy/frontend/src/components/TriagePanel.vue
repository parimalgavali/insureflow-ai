<script setup lang="ts">
import type { TriageSnapshot } from "../types";

defineProps<{
  triage: TriageSnapshot;
}>();
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Decision Support</p>
        <h2>AI Triage</h2>
      </div>
      <span v-if="triage.humanReviewRequired" class="review-required">Human review required</span>
    </div>

    <div class="score-grid">
      <div class="score-block">
        <span>Severity</span>
        <strong :class="triage.severity.toLowerCase()">{{ triage.severity }}</strong>
      </div>
      <div class="score-block">
        <span>Fraud</span>
        <strong :class="triage.fraud.toLowerCase()">{{ triage.fraud }}</strong>
      </div>
      <div class="score-block">
        <span>Litigation</span>
        <strong :class="triage.litigation.toLowerCase()">{{ triage.litigation }}</strong>
      </div>
    </div>

    <div class="reason-list">
      <span v-for="reason in triage.reasonCodes" :key="reason">{{ reason }}</span>
    </div>

    <p class="queue-recommendation">Queue: {{ triage.recommendedQueue }}</p>
  </section>
</template>
