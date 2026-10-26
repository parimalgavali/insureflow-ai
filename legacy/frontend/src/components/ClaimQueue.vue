<script setup lang="ts">
import { computed, ref } from "vue";

import type { ClaimDetail, RiskLabel } from "../types";

const props = defineProps<{
  claims: ClaimDetail[];
  selectedClaimNumber: string;
}>();

const emit = defineEmits<{
  select: [claimNumber: string];
}>();

const search = ref("");
const riskFilter = ref<"ALL" | RiskLabel>("ALL");

const filteredClaims = computed(() => {
  const query = search.value.trim().toLowerCase();
  return props.claims.filter((claim) => {
    const matchesSearch =
      !query ||
      claim.claimNumber.toLowerCase().includes(query) ||
      claim.customer.name.toLowerCase().includes(query) ||
      claim.claimType.toLowerCase().includes(query);
    const matchesRisk = riskFilter.value === "ALL" || claim.priority === riskFilter.value;
    return matchesSearch && matchesRisk;
  });
});
</script>

<template>
  <section class="queue-panel" aria-label="Claim Queue">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Open Work</p>
        <h2>Claim Queue</h2>
      </div>
      <span class="count-pill">{{ filteredClaims.length }}</span>
    </div>

    <label class="field-label" for="claim-search">Search</label>
    <input
      id="claim-search"
      v-model="search"
      aria-label="Search claims"
      class="input"
      placeholder="Claim, customer, type"
      type="search"
    />

    <div class="segmented" aria-label="Risk filter">
      <button
        v-for="risk in ['ALL', 'HIGH', 'MEDIUM', 'LOW']"
        :key="risk"
        class="segment"
        :class="{ active: riskFilter === risk }"
        type="button"
        @click="riskFilter = risk as 'ALL' | RiskLabel"
      >
        {{ risk }}
      </button>
    </div>

    <div class="queue-list">
      <button
        v-for="claim in filteredClaims"
        :key="claim.claimNumber"
        class="claim-row"
        :class="{ selected: claim.claimNumber === selectedClaimNumber }"
        data-test="claim-row"
        type="button"
        @click="emit('select', claim.claimNumber)"
      >
        <span class="row-main">
          <strong>{{ claim.claimNumber }}</strong>
          <span>{{ claim.customer.name }}</span>
        </span>
        <span class="row-meta">
          <span class="risk-dot" :class="claim.priority.toLowerCase()" />
          <span>{{ claim.claimType }}</span>
        </span>
      </button>
    </div>
  </section>
</template>
