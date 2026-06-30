<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import HumanReviewModal from "../components/HumanReviewModal.vue";
import { demoClaims } from "../demoData";
import type { HumanReviewSubmission } from "../types";

const route = useRoute();
const router = useRouter();
const submittedReview = ref<HumanReviewSubmission | null>(null);

const selectedClaim = computed(() => {
  const claimNumber = route.params.claimNumber;
  return demoClaims.find((claim) => claim.claimNumber === claimNumber) ?? demoClaims[0];
});

function closeReview() {
  router.push(`/claims/${selectedClaim.value.claimNumber}`);
}

function submitReview(review: HumanReviewSubmission) {
  submittedReview.value = review;
}
</script>

<template>
  <main class="page-shell review-route">
    <section class="page-heading">
      <div>
        <p class="eyebrow">{{ selectedClaim.claimNumber }}</p>
        <h2>Human Review</h2>
      </div>
      <RouterLink class="ghost-button link-action" :to="`/claims/${selectedClaim.claimNumber}`">
        Back to Claim
      </RouterLink>
    </section>

    <section v-if="submittedReview" class="panel">
      <p class="eyebrow">Recorded Action</p>
      <h2>{{ submittedReview.action }}</h2>
      <p class="route-page-copy">{{ submittedReview.reason }}</p>
    </section>

    <HumanReviewModal
      :claim-number="selectedClaim.claimNumber"
      @close="closeReview"
      @submit="submitReview"
    />
  </main>
</template>
