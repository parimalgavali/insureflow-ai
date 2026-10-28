<script setup lang="ts">
import { onMounted, ref } from "vue";
import { fetchEval, type EvalReport } from "../api/client";

const report = ref<EvalReport | null>(null);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    report.value = await fetchEval();
  } catch (e) {
    error.value = (e as Error).message;
  }
});

const pct = (x: number | undefined) => (x === undefined ? "–" : `${Math.round(x * 100)}%`);
</script>

<template>
  <section class="panel eval" aria-label="Retrieval evaluation">
    <h2>Retrieval evaluation <small>(dev page – is the retriever measured? yes)</small></h2>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <p v-else-if="!report" class="empty">Running the eval questions against the live retriever…</p>
    <template v-else>
      <p class="summary" data-testid="eval-summary">
        <span class="badge" :class="report.passed ? 'likely_covered' : 'likely_not_covered'">{{ report.passed ? "pass" : "fail" }}</span>
        top-1 {{ pct(report.summary.top1) }} · top-3 <strong>{{ pct(report.summary.top3) }}</strong> (threshold {{ pct(report.threshold) }}) · MRR
        {{ report.summary.mrr?.toFixed(2) }} · DE top-3 {{ pct(report.summary.de_top3) }} · EN top-3 {{ pct(report.summary.en_top3) }} · n =
        {{ report.results.length }}, k = {{ report.k }}
      </p>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>lang</th>
            <th>question</th>
            <th>expected</th>
            <th>retrieved (top {{ report.k }})</th>
            <th>rank</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in report.results" :key="r.id" :class="r.hit ? 'hit' : 'miss'" :data-testid="`eval-${r.id}`">
            <td>{{ r.id }}</td>
            <td>{{ r.lang.toUpperCase() }}</td>
            <td>{{ r.question }}</td>
            <td><code v-for="c in r.expected" :key="c">{{ c }}</code></td>
            <td>
              <code v-for="c in r.retrieved" :key="c" :class="{ expected: r.expected.some((e) => c === e || c.startsWith(e + '.')) }">{{ c }}</code>
            </td>
            <td>{{ r.rank ?? "miss" }}</td>
          </tr>
        </tbody>
      </table>
      <p class="disclaimer">
        Same code path as <code>python -m rag.eval</code>; CI fails below the top-3 threshold. Questions live in
        <code>rag/eval/questions.jsonl</code>, LLM query rewrites are replayed from <code>rag/eval/rewrites.json</code>.
      </p>
    </template>
  </section>
</template>
