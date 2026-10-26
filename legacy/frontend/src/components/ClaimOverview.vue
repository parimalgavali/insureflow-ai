<script setup lang="ts">
import type { ClaimDetail } from "../types";

defineProps<{
  claim: ClaimDetail;
}>();
</script>

<template>
  <section class="panel overview-panel">
    <div class="claim-title-row">
      <div>
        <p class="eyebrow">{{ claim.status }}</p>
        <h2>{{ claim.claimNumber }}</h2>
      </div>
      <span class="status-badge" :class="claim.priority.toLowerCase()">{{ claim.priority }} Priority</span>
    </div>

    <p class="claim-description">{{ claim.description }}</p>

    <div class="info-grid">
      <div>
        <span>Customer</span>
        <strong>{{ claim.customer.name }}</strong>
        <small>{{ claim.customer.customerNumber }} · {{ claim.customer.location }}</small>
      </div>
      <div>
        <span>Policy</span>
        <strong>{{ claim.policy.policyNumber }}</strong>
        <small>{{ claim.policy.type }} · {{ claim.policy.status }}</small>
      </div>
      <div>
        <span>Coverage</span>
        <strong>{{ claim.policy.coverageStatus }}</strong>
        <small>Deductible {{ claim.policy.deductible }} · Limit {{ claim.policy.limit }}</small>
      </div>
      <div>
        <span>Loss</span>
        <strong>{{ claim.estimatedLoss }}</strong>
        <small>{{ claim.lossDate }} · reported {{ claim.reportedDate }}</small>
      </div>
    </div>
  </section>
</template>
