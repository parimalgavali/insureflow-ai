# Responsible AI Statement

InsureFlow AI treats AI as decision support only. AI outputs in this repository must not be used for real claim approval, denial, fraud accusation, legal advice, medical advice, customer communication, pricing, underwriting, or production insurance decisions.

The project uses synthetic data and deterministic local services to demonstrate responsible AI design patterns in insurance workflows.

## Project Boundary

InsureFlow AI is a Guidewire-inspired portfolio simulation. It is not an official Guidewire product, connector, implementation, certification, or integration.

The system is built to demonstrate engineering and domain understanding, not to process real insurance data or make real operational decisions.

## Data Boundary

The data generator creates synthetic customers, policies, claims, documents, labels, notes, payments, coverages, adjusters, and events. Synthetic data helps make the project public and reproducible, but it does not represent real claim distributions, real fraud patterns, real medical facts, or real policyholder behavior.

Implication: model metrics and examples are useful for engineering demonstration only.

Related docs:

- [Synthetic data generation](../data/synthetic-data-generation.md)
- [Data dictionary](../data/data-dictionary.md)

## Rule-Based Triage

Rule-based triage provides explainable baseline decision support. It produces severity, fraud, and litigation signals with reason codes. Rules are deterministic and testable, which makes them useful for demonstrating transparency and audit behavior.

Limitations:

- rules are simplified;
- thresholds are demo-oriented;
- reason codes are not legal or claims-handling advice;
- outputs require human review in high-risk scenarios.

Related doc:

- [AI triage API](../api/ai-triage.md)

## ML Triage Models

The ML models are trained on synthetic, rule-labeled data. They demonstrate feature engineering, training, artifact packaging, metrics, model cards, and serving integration. They are not production fraud or severity models.

Controls:

- model cards document intended use and limitations;
- artifacts include metadata and feature columns;
- service falls back to rule-based scoring if artifacts are absent;
- labels stay bounded to `LOW`, `MEDIUM`, and `HIGH`;
- human review remains part of high-risk workflows.

Related docs:

- [Model training](../ml/model-training.md)
- [Severity model card](../ml/severity-model-card.md)
- [Fraud-risk model card](../ml/fraud-risk-model-card.md)

## Document Intelligence

The document intelligence service uses deterministic local providers to simulate LLM-style extraction and summarization. It validates structured outputs and retries invalid responses.

Limitations:

- extracted values are demo outputs;
- summaries are not legal or medical opinions;
- missing-document checks are workflow aids, not compliance determinations;
- real deployments would require provider evaluation, prompt evaluation, privacy controls, and human review.

Related doc:

- [Document intelligence API](../api/document-intelligence.md)

## RAG Adjuster Assistant

The RAG assistant retrieves from synthetic claim documents and returns grounded answers with source references. It should report missing evidence when support is unavailable.

Controls:

- answers include sources;
- missing evidence is explicit;
- retrieval and chunking are testable;
- output is positioned as adjuster assistance, not final claim decisioning.

Related doc:

- [RAG assistant API](../api/rag-assistant.md)

## Human Review And Audit

The backend includes human review and override controls for high-risk or non-standard outcomes. Audit logging, correlation IDs, and AI input/output snapshots support traceability.

Governance features include:

- JWT role-based access control;
- request correlation IDs;
- structured audit logs;
- AI triage input and output snapshots;
- model and prompt registry views;
- human review override enforcement.

Related doc:

- [Security, audit, and governance](../api/security-audit-governance.md)

## Prohibited Uses

Do not use this project or its AI outputs for:

- real claim approval or denial;
- fraud accusation;
- legal advice;
- medical advice;
- customer eligibility decisions;
- policy pricing or underwriting;
- compliance determinations;
- production insurance operations.

## Responsible Demo Language

Use this language in demos:

"The AI features in InsureFlow AI are decision-support demonstrations over synthetic data. They show how rules, ML, document intelligence, RAG, audit, and human review can be integrated responsibly, but they are not production insurance decision systems."

## Future Production Considerations

A real deployment would require:

- real data governance and privacy review;
- bias and performance evaluation on representative data;
- model risk management;
- prompt and retrieval evaluation;
- human factors testing;
- monitoring and drift detection;
- explainability review;
- regulatory and legal review;
- incident response and rollback plans.
