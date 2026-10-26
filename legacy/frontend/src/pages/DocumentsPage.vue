<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import DocumentPanel from "../components/DocumentPanel.vue";
import RagAssistant from "../components/RagAssistant.vue";
import { claimRepository } from "../services/claimRepository";
import type { ClaimDetail, DocumentIntelligenceSnapshot, RagAnswer } from "../types";

const claims = ref<ClaimDetail[]>([]);
const selectedClaimNumber = ref("");
const documents = ref<DocumentIntelligenceSnapshot | null>(null);
const rag = ref<RagAnswer | null>(null);
const question = ref("What documents are missing?");
const loading = ref(true);
const asking = ref(false);
const error = ref("");

const selectedClaim = computed(
  () => claims.value.find((claim) => claim.claimNumber === selectedClaimNumber.value) ?? null,
);

onMounted(async () => {
  await loadClaims();
});

watch(selectedClaimNumber, async (claimNumber) => {
  if (claimNumber) {
    await loadWorkspace(claimNumber);
  }
});

async function loadClaims() {
  loading.value = true;
  error.value = "";
  try {
    claims.value = await claimRepository.listClaims();
    selectedClaimNumber.value = claims.value[0]?.claimNumber ?? "";
  } catch (caught) {
    error.value = messageFromError(caught);
  } finally {
    loading.value = false;
  }
}

async function loadWorkspace(claimNumber: string) {
  loading.value = true;
  error.value = "";
  try {
    const [workspace, answer] = await Promise.all([
      claimRepository.getDocumentWorkspace(claimNumber),
      claimRepository.askRagQuestion(claimNumber, question.value),
    ]);
    documents.value = workspace;
    rag.value = answer;
  } catch (caught) {
    error.value = messageFromError(caught);
  } finally {
    loading.value = false;
  }
}

async function askQuestion() {
  if (!selectedClaimNumber.value || question.value.trim().length === 0) {
    return;
  }
  asking.value = true;
  error.value = "";
  try {
    rag.value = await claimRepository.askRagQuestion(selectedClaimNumber.value, question.value.trim());
  } catch (caught) {
    error.value = messageFromError(caught);
  } finally {
    asking.value = false;
  }
}

function messageFromError(caught: unknown) {
  return caught instanceof Error ? caught.message : "Unable to load document workspace.";
}
</script>

<template>
  <main class="page-shell">
    <section class="page-heading">
      <div>
        <p class="eyebrow">Document AI</p>
        <h2>Document Workspace</h2>
      </div>
      <div class="topbar-meta">
        <span class="count-pill">{{ claims.length }}</span>
        <span class="status-badge low">{{ claimRepository.mode }}</span>
      </div>
    </section>

    <section class="panel">
      <div class="workspace-controls">
        <label>
          <span class="field-label">Claim</span>
          <select v-model="selectedClaimNumber" class="input">
            <option v-for="claim in claims" :key="claim.claimNumber" :value="claim.claimNumber">
              {{ claim.claimNumber }} · {{ claim.customer.name }}
            </option>
          </select>
        </label>
        <div v-if="selectedClaim" class="route-page-copy">
          {{ selectedClaim.description }}
        </div>
      </div>
    </section>

    <p v-if="error" class="decision-warning">{{ error }}</p>
    <p v-else-if="loading" class="route-page-copy">Loading document workspace...</p>

    <section v-else-if="documents && rag" class="workspace-columns">
      <DocumentPanel :documents="documents" />

      <div class="workspace">
        <section class="panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">Grounded Q&A</p>
              <h2>Ask RAG</h2>
            </div>
          </div>

          <form class="rag-question-form" @submit.prevent="askQuestion">
            <label>
              <span class="field-label">Question</span>
              <input v-model="question" class="input" type="text" />
            </label>
            <button class="primary-action" type="submit" :disabled="asking">
              {{ asking ? "Asking..." : "Ask" }}
            </button>
          </form>
        </section>

        <RagAssistant :rag="rag" />
      </div>
    </section>
  </main>
</template>
