<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

import { demoClaims } from "./demoData";

const route = useRoute();

const selectedClaim = computed(() => {
  const claimNumber = route.params.claimNumber;
  if (typeof claimNumber !== "string") {
    return null;
  }
  return demoClaims.find((claim) => claim.claimNumber === claimNumber) ?? null;
});
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
        <strong>{{ selectedClaim?.claimNumber ?? "Claim Operations" }}</strong>
      </div>
    </header>

    <nav class="app-nav" aria-label="Primary navigation">
      <RouterLink to="/claims">Claims</RouterLink>
      <RouterLink to="/documents">Documents</RouterLink>
      <RouterLink to="/governance">Governance</RouterLink>
      <RouterLink to="/integrations">Integrations</RouterLink>
      <RouterLink to="/settings">Settings</RouterLink>
    </nav>

    <RouterView />
  </div>
</template>
