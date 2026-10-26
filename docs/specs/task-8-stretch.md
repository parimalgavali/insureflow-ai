# Task 8 — Stretch (only after task 7)

Pick at most one at a time; each is its own PR.

1. **Damage-photo tagger (deep learning).** Fine-tune a pretrained small CNN (torchvision `mobilenet_v3_small` or `resnet18`) on a car-damage image set with an explicit license; classes ≈ dent / scratch / glass / severe. Serve from the API; the agent uses the tag as a fact ("photo suggests glass damage → Teilkasko A.2.2.x"). Report accuracy honestly on a held-out split; add a model card.
2. **Severity / frequency model on freMTPL2.** Poisson GLM baseline vs gradient boosting; show expected claim cost by driver/vehicle profile in the card as context, never as a decision.
3. **DE/EN UI toggle** with i18n JSON; agent language follows the toggle unless the user writes otherwise.
4. **RAG eval page.** A tiny `/eval` route (dev only) listing the 25 questions, retrieved clauses and hit/miss — useful in interviews to show the retriever is measured.
5. **More Musterbedingungen.** Add Hausrat (VHB) or Privathaftpflicht (AHB) from the same GDV page; the agent asks which product the claim concerns.
