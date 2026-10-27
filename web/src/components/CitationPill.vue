<script setup lang="ts">
import { ref } from "vue";
import type { Citation } from "../api/client";

defineProps<{ citation: Citation }>();
const open = ref(false);
</script>

<template>
  <span class="pill-wrap" style="position: relative; display: inline-block">
    <button
      type="button"
      class="pill"
      :aria-expanded="open"
      :aria-label="`Clause ${citation.clause_id}: ${citation.title}`"
      @click="open = !open"
      @blur="open = false"
    >
      {{ citation.clause_id }}
    </button>
    <span v-if="open" class="popover" role="dialog" data-testid="popover">
      <strong>AKB 2015 {{ citation.clause_id }} – {{ citation.title || "clause" }}</strong>
      {{ citation.excerpt }}
      <br /><small v-if="citation.page">page {{ citation.page }}</small>
    </span>
  </span>
</template>
