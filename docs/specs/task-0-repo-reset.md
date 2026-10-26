# Task 0 — Repo reset & docs

**Goal:** turn the repository from "v1 Guidewire prototype" into "v2 ClaimPilot, in progress" without losing history.

**Scope**
- Tag current `main` as `v1-guidewire-prototype`.
- `git mv` all v1 code, docs and compose/CI files under `legacy/`; add `legacy/README.md` explaining why it is archived. Move v1 workflows to `legacy/.github/workflows/` so they stop running.
- New root `README.md` (pitch, example conversation, component table, architecture sketch, data, layout, honesty section).
- `docs/DECISIONS.md`, `docs/DATA.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/specs/task-0..8`, `docs/planning/2026-10-27-v2-direction.md` (the audit + plan).

**Not in scope:** any runnable code. CI is intentionally absent until task 5.

**Done when:** PR merged; tag pushed; root tree contains only `README.md`, `docs/`, `legacy/`, `.gitignore`.

**Risks:** none technical. Make sure the tag is pushed (`git push origin v1-guidewire-prototype`).
