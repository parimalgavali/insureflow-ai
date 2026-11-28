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
    :aria-label="citation.source === 'uploaded_policy' ? t('card.showPolicyPassage', { id: citation.clause_id, title: citation.title, name: citation.source_name || '', page: citation.page || '' }) : t('card.showClause', { id: citation.clause_id, title: citation.title })"
    @click="emit('select', citation)"
  >
    {{ citation.clause_id }}<template v-if="citation.source === 'uploaded_policy' && citation.page"> · {{ t("card.page", { page: citation.page }) }}</template>
  </button>
</template>
