# Service Architecture

InsureFlow AI starts as a pragmatic modular product with a Spring Boot backend foundation, local infrastructure, and reserved folders for later AI, frontend, and data-generation work.

## Planned Modules

- `backend/api` hosts the initial Spring Boot API, OpenAPI documentation, Flyway migrations, and relational insurance schema.
- `ai-services` will host FastAPI services for triage, ML inference, document intelligence, and RAG in later phases.
- `frontend` will host the Vue adjuster workbench after backend and AI contracts stabilize.
- `synthetic-data-generator` will create generated relational and document data for demos, model development, and repeatable tests.
- PostgreSQL stores the core insurance domain, audit records, prompt/model metadata, and future RAG data.
- RabbitMQ provides local message broker infrastructure for future asynchronous workflow and integration events.

The first backend increment is intentionally narrow: application bootstrapping, schema creation, migration tests, and documentation. Business workflows and service integrations are added in later phases.
