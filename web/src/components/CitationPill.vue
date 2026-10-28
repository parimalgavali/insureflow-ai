<script setup lang="ts">
import type { Citation } from "../api/client";

import { t } from "../i18n";

defineProps<{ citation: Citation; active?: boolean }>();
const emit = defineEmits<{ select: [citation: Citation] }>();
</script>

<template>
  <button
    type="button"
    class="pill"
    :class="{ active }"
    :aria-pressed="active"
    :aria-label="t('card.showClause', { id: citation.clause_id, title: citation.title })"
    @click="emit('select', citation)"
  >
    {{ citation.clause_id }}
  </button>
</template>
