# Screenshot Checklist

Phase 14 does not require committing screenshots. Use this checklist when preparing portfolio images for GitHub, LinkedIn, a resume PDF, or a demo deck.

Recommended output folder if screenshots are added later:

```text
docs/demo/screenshots/
```

Do not include private data. Use only synthetic demo data.

## Required Screenshots

| File Name | View | What It Should Show |
| --- | --- | --- |
| `01-readme-architecture.png` | GitHub README | Architecture diagram and project framing |
| `02-adjuster-queue.png` | Vue workbench | Claim queue with severity and workflow context |
| `03-claim-detail.png` | Vue workbench | Claim summary, policy/coverage context, timeline |
| `04-ai-triage.png` | Vue workbench or API output | Severity, fraud, litigation, reason codes, human review |
| `05-document-intelligence.png` | Document intelligence output | Extracted fields, summary, missing-document checks |
| `06-rag-assistant.png` | RAG assistant output | Grounded answer with source references |
| `07-governance-audit.png` | API docs or frontend | Audit, human review, model/prompt registry context |
| `08-swagger-api.png` | Swagger UI | API groups for claims, triage, governance, integration |
| `09-grafana-dashboard.png` | Grafana | API/Actuator dashboard or service metrics |
| `10-github-actions.png` | GitHub Actions | Passing CI, quality, and security checks |

## Capture Tips

- Use a clean browser window with bookmarks hidden.
- Avoid showing local secrets, tokens, personal email, or unrelated tabs.
- Prefer 1440px wide screenshots for GitHub and portfolio pages.
- Crop only when it improves readability.
- Keep the Guidewire-inspired boundary visible in README or narrative screenshots.

## Demo Deck Order

1. README architecture.
2. Adjuster queue.
3. Claim detail.
4. AI triage.
5. RAG or document intelligence.
6. Governance/audit.
7. Quality/observability.

This sequence mirrors the five-minute demo script.
