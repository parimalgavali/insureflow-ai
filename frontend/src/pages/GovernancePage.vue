<script setup lang="ts">
import AuditPanel from "../components/AuditPanel.vue";
import { demoClaims } from "../demoData";
</script>

<template>
  <main class="page-shell">
    <section class="page-heading">
      <div>
        <p class="eyebrow">Responsible AI</p>
        <h2>Governance</h2>
      </div>
    </section>

    <div class="page-card-grid">
      <AuditPanel
        v-for="claim in demoClaims"
        :key="claim.claimNumber"
        :events="claim.audit"
        :last-review="null"
      />
    </div>
  </main>
</template>
