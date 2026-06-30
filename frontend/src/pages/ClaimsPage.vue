<script setup lang="ts">
import { useRouter } from "vue-router";

import ClaimQueue from "../components/ClaimQueue.vue";
import { demoClaims } from "../demoData";

const router = useRouter();

function openClaim(claimNumber: string) {
  router.push(`/claims/${claimNumber}`);
}
</script>

<template>
  <main class="page-shell">
    <section class="page-heading">
      <div>
        <p class="eyebrow">Open Work</p>
        <h2>Claim Queue</h2>
      </div>
      <span class="count-pill">{{ demoClaims.length }}</span>
    </section>

    <div class="queue-page-grid">
      <ClaimQueue
        :claims="demoClaims"
        :selected-claim-number="demoClaims[0].claimNumber"
        @select="openClaim"
      />
      <section class="panel">
        <p class="eyebrow">Selected Workflow</p>
        <h2>Adjuster Workbench</h2>
        <p class="route-page-copy">
          Select a claim to open the full detail workspace with triage, documents, RAG support, timeline, and audit.
        </p>
      </section>
    </div>
  </main>
</template>
