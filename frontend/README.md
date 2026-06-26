# Frontend

Vue adjuster workbench area for InsureFlow AI.

## Current Status

Phase 9 implements a demo-data-first Vue adjuster workbench. It opens directly to an operational claim queue and selected claim workspace so the insurance workflow is visible without requiring backend or AI services to be running.

## Local Setup

Install dependencies:

```bash
npm install
```

Run tests:

```bash
npm test -- --run
```

Build for production:

```bash
npm run build
```

Start the development server:

```bash
npm run dev
```

## Implemented Responsibilities

- Claim queue.
- Claim detail workspace.
- Policy and coverage panels.
- AI triage review.
- Document and timeline views.
- Human review and override workflows.
- RAG assistant answer with source references.
- AI/RAG/human review audit panel.

## Demo Story

The default claim is a high-priority motor collision with missing police report, AI triage, document intelligence highlights, a grounded RAG answer, and a human review checkpoint.

The app uses local typed demo data in `src/demoData.ts`. Live backend integration is intentionally deferred until the frontend workflow is stable.
