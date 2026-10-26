<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AuditPanel from "../components/AuditPanel.vue";
import ClaimOverview from "../components/ClaimOverview.vue";
import DocumentPanel from "../components/DocumentPanel.vue";
import RagAssistant from "../components/RagAssistant.vue";
import TimelinePanel from "../components/TimelinePanel.vue";
import TriagePanel from "../components/TriagePanel.vue";
import { claimRepository } from "../services/claimRepository";
import type { ClaimDetail, HumanReviewSubmission } from "../types";

const route = useRoute();
const lastReview = ref<HumanReviewSubmission | null>(null);
const claims = ref<ClaimDetail[]>([]);
const selectedClaim = ref<ClaimDetail | null>(null);
const isLoading = ref(true);
const errorMessage = ref("");

async function loadClaim() {
  const claimNumber = route.params.claimNumber;
  if (typeof claimNumber !== "string") {
    errorMessage.value = "Claim route is missing a claim number.";
    isLoading.value = false;
    return;
  }

  isLoading.value = true;
  errorMessage.value = "";
  try {
    const [claimList, claim] = await Promise.all([
      claimRepository.listClaims(),
      claimRepository.getClaim(claimNumber),
    ]);
    claims.value = claimList;
    selectedClaim.value = claim;
    if (!claim) {
      errorMessage.value = `Claim ${claimNumber} was not found.`;
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Unable to load claim.";
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadClaim);
watch(() => route.params.claimNumber, loadClaim);
</script>

<template>
  <main v-if="isLoading" class="page-shell">
    <section class="panel state-panel">Loading claim...</section>
  </main>
  <main v-else-if="errorMessage || !selectedClaim" class="page-shell">
    <section class="panel state-panel error-state">{{ errorMessage }}</section>
  </main>
  <main v-else class="workbench-grid">
    <section class="queue-panel compact-route-panel" aria-label="Claim navigation">
      <p class="eyebrow">Open Work</p>
      <h2>Claim Queue</h2>
      <div class="queue-list">
        <RouterLink
          v-for="claim in claims"
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
