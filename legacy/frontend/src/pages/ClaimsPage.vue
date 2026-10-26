<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import ClaimQueue from "../components/ClaimQueue.vue";
import { claimRepository } from "../services/claimRepository";
import type { ClaimDetail } from "../types";

const router = useRouter();
const claims = ref<ClaimDetail[]>([]);
const isLoading = ref(true);
const errorMessage = ref("");

function openClaim(claimNumber: string) {
  router.push(`/claims/${claimNumber}`);
}

onMounted(async () => {
  try {
    claims.value = await claimRepository.listClaims();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Unable to load claims.";
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <main class="page-shell">
    <section class="page-heading">
      <div>
        <p class="eyebrow">Open Work</p>
        <h2>Claim Queue</h2>
      </div>
      <span class="count-pill">{{ claims.length }}</span>
    </section>

    <section v-if="isLoading" class="panel state-panel">Loading claims...</section>
    <section v-else-if="errorMessage" class="panel state-panel error-state">{{ errorMessage }}</section>
    <section v-else-if="claims.length === 0" class="panel state-panel">No open claims found.</section>
    <div v-else class="queue-page-grid">
      <ClaimQueue
        :claims="claims"
        :selected-claim-number="claims[0].claimNumber"
        @select="openClaim"
      />
      <section class="panel">
        <p class="eyebrow">Selected Workflow</p>
        <h2>Adjuster Workbench</h2>
        <p class="route-page-copy">
          Select a claim to open the full detail workspace with triage, documents, RAG support, timeline, and audit.
        </p>
        <p class="review-note">
          Data mode: <strong>{{ claimRepository.mode.toUpperCase() }}</strong>
        </p>
      </section>
    </div>
  </main>
</template>
