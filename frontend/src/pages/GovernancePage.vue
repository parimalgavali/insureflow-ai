<script setup lang="ts">
import { onMounted, ref } from "vue";

import { claimRepository } from "../services/claimRepository";
import type { GovernanceDashboard, GovernanceFilters } from "../types";

const dashboard = ref<GovernanceDashboard | null>(null);
const filters = ref<GovernanceFilters>({
  entityType: "CLAIMS",
  actorId: "",
  action: "",
  correlationId: "",
});
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  await loadDashboard();
});

async function loadDashboard() {
  loading.value = true;
  error.value = "";
  try {
    dashboard.value = await claimRepository.getGovernanceDashboard(normalizedFilters());
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : "Unable to load governance dashboard.";
  } finally {
    loading.value = false;
  }
}

function normalizedFilters(): GovernanceFilters {
  return Object.fromEntries(
    Object.entries(filters.value)
      .map(([key, value]) => [key, value?.trim()])
      .filter(([, value]) => value),
  );
}
</script>

<template>
  <main class="page-shell">
    <section class="page-heading">
      <div>
        <p class="eyebrow">Responsible AI</p>
        <h2>Governance Dashboard</h2>
      </div>
      <div class="topbar-meta">
        <span class="status-badge low">{{ claimRepository.mode }}</span>
      </div>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Audit Search</p>
          <h2>Audit Events</h2>
        </div>
      </div>

      <form class="governance-filter-grid" @submit.prevent="loadDashboard">
        <label>
          <span class="field-label">Actor</span>
          <input v-model="filters.actorId" class="input" type="text" />
        </label>
        <label>
          <span class="field-label">Entity</span>
          <select v-model="filters.entityType" class="input">
            <option value="">All</option>
            <option value="CLAIMS">CLAIMS</option>
            <option value="GOVERNANCE">GOVERNANCE</option>
            <option value="AUDIT">AUDIT</option>
            <option value="INTEGRATION">INTEGRATION</option>
          </select>
        </label>
        <label>
          <span class="field-label">Action</span>
          <input v-model="filters.action" class="input" type="text" />
        </label>
        <label>
          <span class="field-label">Correlation</span>
          <input v-model="filters.correlationId" class="input" type="text" />
        </label>
        <button class="primary-action" type="submit">Apply Filters</button>
      </form>
    </section>

    <p v-if="error" class="decision-warning">{{ error }}</p>
    <p v-else-if="loading" class="route-page-copy">Loading governance evidence...</p>

    <template v-else-if="dashboard">
      <section class="governance-summary-grid">
        <article class="panel">
          <p class="eyebrow">Registry</p>
          <h2>{{ dashboard.modelVersions.length }}</h2>
          <p class="route-page-copy">Model Versions</p>
        </article>
        <article class="panel">
          <p class="eyebrow">Prompts</p>
          <h2>{{ dashboard.promptVersions.length }}</h2>
          <p class="route-page-copy">Prompt Versions</p>
        </article>
        <article class="panel">
          <p class="eyebrow">Trace</p>
          <h2>{{ dashboard.auditEvents.length }}</h2>
          <p class="route-page-copy">Audit Events</p>
        </article>
        <article class="panel">
          <p class="eyebrow">Claims</p>
          <h2>{{ dashboard.aiEvidence.length }}</h2>
          <p class="route-page-copy">AI Evidence</p>
        </article>
      </section>

      <section class="workspace-columns">
        <section class="panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">Governance Registry</p>
              <h2>Model Versions</h2>
            </div>
          </div>
          <div class="audit-grid">
            <article v-for="model in dashboard.modelVersions" :key="model.id">
              <span>{{ model.type }} · {{ model.active ? "ACTIVE" : "INACTIVE" }}</span>
              <h3>{{ model.name }}</h3>
              <p>{{ model.version }}</p>
              <p>{{ model.artifactUri }}</p>
            </article>
          </div>
        </section>

        <section class="panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">Prompt Registry</p>
              <h2>Prompt Versions</h2>
            </div>
          </div>
          <div class="audit-grid">
            <article v-for="prompt in dashboard.promptVersions" :key="prompt.id">
              <span>{{ prompt.modelName }} · {{ prompt.active ? "ACTIVE" : "INACTIVE" }}</span>
              <h3>{{ prompt.name }}</h3>
              <p>{{ prompt.version }}</p>
              <p>{{ prompt.templatePreview }}</p>
            </article>
          </div>
        </section>
      </section>

      <section class="workspace-columns">
        <section class="panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">Operational Trace</p>
              <h2>Audit Events</h2>
            </div>
          </div>
          <div class="audit-grid">
            <article v-for="event in dashboard.auditEvents" :key="event.id">
              <span>{{ event.createdAt }} · {{ event.status }}</span>
              <h3>{{ event.action }}</h3>
              <p>{{ event.actorId }} · {{ event.entityType }}</p>
              <p>{{ event.correlationId }}</p>
            </article>
            <p v-if="dashboard.auditEvents.length === 0" class="route-page-copy">No audit events match the filters.</p>
          </div>
        </section>

        <section class="panel">
          <div class="panel-heading">
            <div>
              <p class="eyebrow">Decision Evidence</p>
              <h2>AI Evidence</h2>
            </div>
          </div>
          <div class="audit-grid">
            <article v-for="evidence in dashboard.aiEvidence" :key="evidence.claimNumber">
              <span>{{ evidence.recommendedQueue }}</span>
              <h3>{{ evidence.claimNumber }}</h3>
              <p>
                Severity {{ evidence.severity }}, fraud {{ evidence.fraud }},
                litigation {{ evidence.litigation }}.
              </p>
              <div class="reason-list">
                <span v-for="reason in evidence.reasonCodes" :key="reason">{{ reason }}</span>
              </div>
              <p>
                RAG sources {{ evidence.ragSourceCount }} ·
                Human review {{ evidence.humanReviewRequired ? "required" : "not required" }}
              </p>
            </article>
          </div>
        </section>
      </section>
    </template>
  </main>
</template>
