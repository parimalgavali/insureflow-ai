<script setup lang="ts">
import type { DocumentIntelligenceSnapshot } from "../types";

defineProps<{
  documents: DocumentIntelligenceSnapshot;
}>();
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Document AI</p>
        <h2>Documents</h2>
      </div>
    </div>

    <div class="document-columns">
      <div>
        <h3>Received</h3>
        <span v-for="doc in documents.receivedDocuments" :key="doc" class="doc-chip complete">{{ doc }}</span>
      </div>
      <div>
        <h3>Missing</h3>
        <span v-if="documents.missingDocuments.length === 0" class="doc-chip complete">NONE</span>
        <span v-for="doc in documents.missingDocuments" :key="doc" class="doc-chip warning">{{ doc }}</span>
      </div>
    </div>

    <ul class="compact-list">
      <li v-for="highlight in documents.extractionHighlights" :key="highlight">{{ highlight }}</li>
    </ul>

    <div class="summary-list">
      <article v-for="section in documents.summarySections" :key="section.title">
        <h3>{{ section.title }}</h3>
        <p>{{ section.body }}</p>
      </article>
    </div>
  </section>
</template>
