<script setup lang="ts">
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
        <h2>Planned for Phase 16</h2>
      </div>
    </section>
  </main>
</template>
