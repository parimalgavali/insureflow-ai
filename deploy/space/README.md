---
title: ClaimPilot
emoji: 🚗
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: File a motor claim by chat — RAG over GDV AKB 2015, LangGraph, human review
---

# ClaimPilot

Conversational motor-claim intake: a LangGraph agent extracts the facts, cites the real GDV AKB 2015
policy wording (pgvector RAG), shows an explainable fraud-risk signal and hands the case to a human
adjuster. Source, model cards and decision log: https://github.com/parimalgavali/insureflow-ai

Space secrets: `DATABASE_URL` (Postgres with pgvector, e.g. Neon), `ANTHROPIC_API_KEY`,
optional `DEMO_API_TOKEN`, `ANTHROPIC_MODEL`. This Space is mirrored from `main` by GitHub Actions.
