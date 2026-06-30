<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AuditPanel from "../components/AuditPanel.vue";
import ClaimOverview from "../components/ClaimOverview.vue";
import DocumentPanel from "../components/DocumentPanel.vue";
import RagAssistant from "../components/RagAssistant.vue";
import TimelinePanel from "../components/TimelinePanel.vue";
import TriagePanel from "../components/TriagePanel.vue";
import { demoClaims } from "../demoData";
import type { HumanReviewSubmission } from "../types";

const route = useRoute();
const lastReview = ref<HumanReviewSubmission | null>(null);

const selectedClaim = computed(() => {
  const claimNumber = route.params.claimNumber;
  return demoClaims.find((claim) => claim.claimNumber === claimNumber) ?? demoClaims[0];
});
</script>

<template>
  <main class="workbench-grid">
    <section class="queue-panel compact-route-panel" aria-label="Claim navigation">
      <p class="eyebrow">Open Work</p>
      <h2>Claim Queue</h2>
      <div class="queue-list">
        <RouterLink
          v-for="claim in demoClaims"
          :key="claim.claimNumber"
          class="claim-row route-claim-link"
          :class="{ selected: claim.claimNumber === selectedClaim.claimNumber }"
          :to="`/claims/${claim.claimNumber}`"
        >
          <span class="row-main">
            <strong>{{ claim.claimNumber }}</strong>
            <span>{{ claim.customer.name }}</span>
          </span>
          <span class="row-meta">
            <span class="risk-dot" :class="claim.priority.toLowerCase()" />
            <span>{{ claim.claimType }}</span>
          </span>
        </RouterLink>
      </div>
    </section>

    <section class="workspace" aria-label="Claim workspace">
      <ClaimOverview :claim="selectedClaim" />
      <div class="workspace-columns">
        <DocumentPanel :documents="selectedClaim.documents" />
        <TimelinePanel :events="selectedClaim.timeline" />
      </div>
      <AuditPanel :events="selectedClaim.audit" :last-review="lastReview" />
    </section>

    <aside class="intelligence-rail" aria-label="Claim intelligence">
      <TriagePanel :triage="selectedClaim.triage" />
      <RagAssistant :rag="selectedClaim.rag" />
      <section class="panel review-panel">
        <div>
          <p class="eyebrow">Human Review</p>
          <h2>Decision support checkpoint</h2>
        </div>
        <p>
          AI outputs are recommendations only. Record the adjuster action and reason before any workflow move.
        </p>
        <RouterLink class="primary-action link-action" :to="`/claims/${selectedClaim.claimNumber}/review`">
          Open Review
        </RouterLink>
        <p v-if="lastReview" class="review-note">
          Last action: <strong>{{ lastReview.action }}</strong>
        </p>
      </section>
    </aside>
  </main>
</template>
