<script setup lang="ts">
import { demoReadinessChecks } from "../services/demoReadiness";
import { claimRepository } from "../services/claimRepository";
</script>

<template>
  <main class="page-shell">
    <section class="page-heading">
      <div>
        <p class="eyebrow">Workspace</p>
        <h2>Settings</h2>
      </div>
    </section>

    <section class="panel settings-grid">
      <div>
        <p class="eyebrow">Data Mode</p>
        <h2>{{ claimRepository.mode.toUpperCase() }}</h2>
      </div>
      <div>
        <p class="eyebrow">API Connection</p>
        <h2>/api proxy ready</h2>
        <p class="route-page-copy">Use VITE_DATA_MODE=live to connect this frontend to the Spring Boot backend.</p>
      </div>
    </section>

    <section class="panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Portfolio Runbook</p>
          <h2>Demo Readiness</h2>
        </div>
      </div>

      <div class="readiness-grid">
        <article v-for="check in demoReadinessChecks" :key="check.label">
          <h3>{{ check.label }}</h3>
          <p>{{ check.detail }}</p>
        </article>
      </div>
    </section>
  </main>
</template>
