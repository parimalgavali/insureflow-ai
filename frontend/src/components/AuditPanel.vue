<script setup lang="ts">
import type { AuditEvent, HumanReviewSubmission } from "../types";

defineProps<{
  events: AuditEvent[];
  lastReview: HumanReviewSubmission | null;
}>();
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Governance</p>
        <h2>Audit View</h2>
      </div>
    </div>

    <div class="audit-grid">
      <article v-for="event in events" :key="`${event.timestamp}-${event.action}`">
        <span>{{ event.timestamp }}</span>
        <strong>{{ event.action }}</strong>
        <p>{{ event.actor }} · {{ event.detail }}</p>
      </article>
      <article v-if="lastReview">
        <span>Current session</span>
        <strong>{{ lastReview.action }}</strong>
        <p>{{ lastReview.reason }}</p>
      </article>
    </div>
  </section>
</template>
