<script setup lang="ts">
import { computed, ref } from "vue";

import AuditPanel from "./components/AuditPanel.vue";
import ClaimOverview from "./components/ClaimOverview.vue";
import ClaimQueue from "./components/ClaimQueue.vue";
import DocumentPanel from "./components/DocumentPanel.vue";
import HumanReviewModal from "./components/HumanReviewModal.vue";
import RagAssistant from "./components/RagAssistant.vue";
import TimelinePanel from "./components/TimelinePanel.vue";
import TriagePanel from "./components/TriagePanel.vue";
import { demoClaims } from "./demoData";
import type { HumanReviewSubmission } from "./types";

const claims = demoClaims;
const selectedClaimNumber = ref(claims[0].claimNumber);
const isReviewOpen = ref(false);
const lastReview = ref<HumanReviewSubmission | null>(null);

const selectedClaim = computed(() => {
  return claims.find((claim) => claim.claimNumber === selectedClaimNumber.value) ?? claims[0];
});

function selectClaim(claimNumber: string) {
  selectedClaimNumber.value = claimNumber;
}

function submitReview(review: HumanReviewSubmission) {
  lastReview.value = review;
  isReviewOpen.value = false;
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">InsureFlow AI</p>
        <h1>Adjuster Workbench</h1>
      </div>
      <div class="topbar-meta">
        <span>Claims Adjuster</span>
        <strong>{{ selectedClaim.claimNumber }}</strong>
      </div>
    </header>

    <main class="workbench-grid">
      <ClaimQueue
        :claims="claims"
        :selected-claim-number="selectedClaim.claimNumber"
        @select="selectClaim"
      />

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
          <button class="primary-action" type="button" @click="isReviewOpen = true">Open Review</button>
          <p v-if="lastReview" class="review-note">
            Last action: <strong>{{ lastReview.action }}</strong>
          </p>
        </section>
      </aside>
    </main>

    <HumanReviewModal
      v-if="isReviewOpen"
      :claim-number="selectedClaim.claimNumber"
      @close="isReviewOpen = false"
      @submit="submitReview"
    />
  </div>
</template>
