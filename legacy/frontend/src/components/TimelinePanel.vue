<script setup lang="ts">
import type { TimelineEvent } from "../types";

defineProps<{
  events: TimelineEvent[];
}>();
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <div>
        <p class="eyebrow">Claim Activity</p>
        <h2>Timeline</h2>
      </div>
    </div>

    <ol class="timeline">
      <li v-for="event in events" :key="`${event.timestamp}-${event.type}`">
        <span>{{ event.timestamp }}</span>
        <strong>{{ event.type }}</strong>
        <p>{{ event.description }}</p>
        <small>{{ event.source }}</small>
      </li>
    </ol>
  </section>
</template>
