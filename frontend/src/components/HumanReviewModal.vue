<script setup lang="ts">
import { ref } from "vue";

import type { HumanReviewSubmission } from "../types";

defineProps<{
  claimNumber: string;
}>();

const emit = defineEmits<{
  close: [];
  submit: [review: HumanReviewSubmission];
}>();

const action = ref("REQUEST_MORE_INFORMATION");
const reason = ref("");

function submitReview() {
  emit("submit", {
    action: action.value,
    reason: reason.value.trim(),
  });
}
</script>

<template>
  <div class="modal-backdrop" role="presentation">
    <section class="modal" role="dialog" aria-modal="true" aria-labelledby="review-title">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">{{ claimNumber }}</p>
          <h2 id="review-title">Human Review</h2>
        </div>
        <button class="ghost-button" type="button" @click="emit('close')">Close</button>
      </div>

      <p class="decision-warning">
        AI outputs are decision support only. Record an adjuster action and reason before moving the claim.
      </p>

      <form @submit.prevent="submitReview">
        <label class="field-label" for="review-action">Action</label>
        <select id="review-action" v-model="action" class="input">
          <option value="ACCEPT_AI_RECOMMENDATION">Accept AI recommendation</option>
          <option value="REQUEST_MORE_INFORMATION">Request more information</option>
          <option value="OVERRIDE_AI_RECOMMENDATION">Override AI recommendation</option>
        </select>

        <label class="field-label" for="review-reason">Reason</label>
        <textarea
          id="review-reason"
          v-model="reason"
          class="input textarea"
          placeholder="Explain the human review decision"
          required
        />

        <button class="primary-action" type="submit">Submit Review</button>
      </form>
    </section>
  </div>
</template>
