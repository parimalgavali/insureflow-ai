<script setup lang="ts">
import DocumentPanel from "../components/DocumentPanel.vue";
import { demoClaims } from "../demoData";
</script>

<template>
  <main class="page-shell">
    <section class="page-heading">
      <div>
        <p class="eyebrow">Document AI</p>
        <h2>Documents</h2>
      </div>
      <span class="count-pill">{{ demoClaims.length }}</span>
    </section>

    <div class="page-card-grid">
      <DocumentPanel
        v-for="claim in demoClaims"
        :key="claim.claimNumber"
        :documents="claim.documents"
      />
    </div>
  </main>
</template>
