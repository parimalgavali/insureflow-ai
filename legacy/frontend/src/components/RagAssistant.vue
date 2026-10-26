<script setup lang="ts">
import type { RagAnswer } from "../types";

defineProps<{
  rag: RagAnswer;
}>();
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Grounded Q&A</p>
        <h2>RAG Assistant</h2>
      </div>
      <span class="status-badge medium">{{ rag.confidence }}</span>
    </div>

    <div class="question-box">{{ rag.question }}</div>
    <p>{{ rag.answer }}</p>

    <div class="source-list">
      <span v-for="source in rag.sources" :key="source.chunkId">
        {{ source.chunkId }} · {{ source.sectionTitle }}
      </span>
    </div>
  </section>
</template>
