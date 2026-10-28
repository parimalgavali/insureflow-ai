<script setup lang="ts">
import type { Citation } from "../api/client";

defineProps<{ citation: Citation; active?: boolean }>();
const emit = defineEmits<{ select: [citation: Citation] }>();
</script>

<template>
  <button
    type="button"
    class="pill"
    :class="{ active }"
    :aria-pressed="active"
    :aria-label="`Show clause ${citation.clause_id}: ${citation.title}`"
    @click="emit('select', citation)"
  >
    {{ citation.clause_id }}
  </button>
</template>
