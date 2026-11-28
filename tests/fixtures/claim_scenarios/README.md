# Repeatable claim-type scenarios

`scenarios.json` is the scenario manifest: two customer messages, expected saved facts, requested documents, selected product and the relevant policy page. Each type has a normal fixture and a `_liability` fixture for the fictional policy's liability-only exclusion.

| Scenario | Matching test product | Relevant fictional policy passage |
| --- | --- | --- |
| Collision | vollkasko | P.1, page 1 |
| Theft | teilkasko | P.2, page 2 |
| Windscreen glass | teilkasko | P.3, page 3 |
| Vandalism | vollkasko | P.4, page 4 |
| Storm/hail | teilkasko | P.5, page 5 |

All cases also use P.6 (deductible/human review). The policy is `../claim_types_policy.pdf`, a synthetic six-page fixture visibly marked as fictional on every page. Its wording is not an insurer contract or a claim about actual coverage rules.

The first recorded extraction leaves the date and risk answers unknown. The second provides those values without repeating the event, damage or party facts, exercising the merge and follow-up path. Theft and vandalism keep unknown incident times as null; the suite must not invent precise times. All requested documents remain Missing because the selected policy PDF is not claim evidence.

The API tests use real PostgreSQL policy preparation and full-text retrieval. They fail if lookup falls through to the shared demo corpus, if a live Anthropic/Ollama completion is attempted, or if scoring runs before required inputs are known. The scorer is a controlled probe, not a trained model performance test. Responses come from `RecordedProvider`; no API key is required.

Run from the repository root with the normal test database configured:

```sh
uv run pytest tests/test_claim_scenarios.py
```

These fixtures verify application orchestration and persistence against controlled outputs. They do not measure the current live model's extraction/composition accuracy or real insurance coverage. Broader bilingual, uncertainty, recovery, access and model-limit evaluations belong to the following backlog stories.

When adding a scenario, keep the customer messages, expected facts, recorded outputs and fictional policy wording consistent. Do not add real customer data. Keep the exact five required types and the two-product matrix covered; the inventory check fails if one is removed accidentally.
