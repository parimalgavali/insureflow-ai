# Task 6 — Frontend

**Goal:** one polished page. Chat on the left, live claim card on the right. Nothing else.

**Deliverables (`web/`, Vue 3 + Vite + TypeScript)**
- `App.vue` → `ChatColumn` + `ClaimCard` (card stacks below chat on narrow screens).
- `ChatColumn`: message list, streaming assistant text (SSE via `fetch` + `ReadableStream`), follow-up **chips** rendered from `question` events (tap to answer), composer with file attach (image/PDF), "thinking" state, retry on error.
- `ClaimCard`: sections that fill in as events arrive — Facts (editable inline), Coverage verdict with **citation pills** (`A.2.3.2`) opening a popover with clause title + text, Risk signal (band + three reasons, with a one-line disclaimer), Missing documents checklist, **Send to adjuster** button → review state → "Reviewed" badge.
- `api/client.ts`: typed event union shared with the backend (generated from OpenAPI or hand-mirrored and tested).
- Language: UI strings in English; the agent replies in the user's language. A DE/EN toggle is task 8.
- Visual: system font stack, two colours plus a status palette, no component library; dark mode via `prefers-color-scheme`. Accessibility: focus order, `aria-live` on streaming region.
- `Dockerfile` (nginx) + `nginx.conf` with `/api` proxy and `proxy_buffering off`; added to compose as `web`.

**Tests:** Vitest for `ClaimCard` event handling and citation popover; `npm run build` type-checks (`vue-tsc`).

**Done when:** the hit-and-run demo flow runs end to end in < 2 minutes from `docker compose up`; Lighthouse accessibility ≥ 90.

**Risks:** streaming + reactive state ordering — reduce events into a single store; don't over-design.
