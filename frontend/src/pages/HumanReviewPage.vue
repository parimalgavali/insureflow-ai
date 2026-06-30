<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import HumanReviewModal from "../components/HumanReviewModal.vue";
import { claimRepository } from "../services/claimRepository";
import type { ClaimDetail, HumanReviewRecord, HumanReviewSubmission } from "../types";

const route = useRoute();
const router = useRouter();
const selectedClaim = ref<ClaimDetail | null>(null);
const reviews = ref<HumanReviewRecord[]>([]);
const isLoading = ref(true);
const isSubmitting = ref(false);
const errorMessage = ref("");

async function loadReviewContext() {
  const claimNumber = route.params.claimNumber;
  if (typeof claimNumber !== "string") {
    errorMessage.value = "Claim route is missing a claim number.";
    isLoading.value = false;
    return;
  }

  isLoading.value = true;
  errorMessage.value = "";
  try {
    const [claim, reviewHistory] = await Promise.all([
      claimRepository.getClaim(claimNumber),
      claimRepository.listHumanReviews(claimNumber),
    ]);
    selectedClaim.value = claim;
    reviews.value = reviewHistory;
    if (!claim) {
      errorMessage.value = `Claim ${claimNumber} was not found.`;
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Unable to load human review.";
  } finally {
    isLoading.value = false;
  }
}

function closeReview() {
  if (selectedClaim.value) {
    router.push(`/claims/${selectedClaim.value.claimNumber}`);
  }
}

async function submitReview(review: HumanReviewSubmission) {
  if (!selectedClaim.value) {
    return;
  }

  isSubmitting.value = true;
  errorMessage.value = "";
  try {
    await claimRepository.submitHumanReview(selectedClaim.value.claimNumber, review);
    reviews.value = await claimRepository.listHumanReviews(selectedClaim.value.claimNumber);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Unable to submit human review.";
  } finally {
    isSubmitting.value = false;
  }
}

onMounted(loadReviewContext);
</script>

<template>
  <main v-if="isLoading" class="page-shell review-route">
    <section class="panel state-panel">Loading human review...</section>
  </main>
  <main v-else-if="errorMessage && !selectedClaim" class="page-shell review-route">
    <section class="panel state-panel error-state">{{ errorMessage }}</section>
  </main>
  <main v-else-if="selectedClaim" class="page-shell review-route">
    <section class="page-heading">
      <div>
        <p class="eyebrow">{{ selectedClaim.claimNumber }}</p>
        <h2>Human Review</h2>
      </div>
      <RouterLink class="ghost-button link-action" :to="`/claims/${selectedClaim.claimNumber}`">
        Back to Claim
      </RouterLink>
    </section>

    <section v-if="errorMessage" class="panel state-panel error-state">{{ errorMessage }}</section>

    <section class="panel">
      <p class="eyebrow">Human Review</p>
      <h2>Review History</h2>
      <p v-if="reviews.length === 0" class="route-page-copy">No human review decisions recorded yet.</p>
      <div v-else class="audit-grid">
        <article v-for="review in reviews" :key="review.id">
          <span>{{ review.reviewedAt.slice(0, 16).replace("T", " ") }}</span>
          <h3>{{ review.decision }}</h3>
          <p>{{ review.notes }}</p>
          <p v-if="review.overrideReason">Override: {{ review.overrideReason }}</p>
        </article>
      </div>
    </section>

    <HumanReviewModal
      :claim-number="selectedClaim.claimNumber"
      @close="closeReview"
      @submit="submitReview"
    />

    <section v-if="isSubmitting" class="panel state-panel">Submitting review...</section>
  </main>
</template>
