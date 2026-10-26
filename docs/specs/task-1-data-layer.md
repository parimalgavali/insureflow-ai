# Task 1 — Data layer

**Goal:** one command fetches every dataset in `docs/DATA.md`; each gets a short data card; nothing large is committed.

**Deliverables**
- `scripts/fetch_data.py` with sub-commands `akb`, `openml`, `kaggle`, `all`.
  - `akb`: download AKB 2015 PDF from the GDV URL into `data/raw/gdv/`; extract text with `pypdf` to `data/processed/akb_2015.txt`; print page/word counts.
  - `openml`: `freMTPL2freq` (41214) and `freMTPL2sev` (41215) via the `openml` package → parquet in `data/processed/`.
  - `kaggle`: `khusheekapoor/vehicle-insurance-fraud-detection` via `kaggle` CLI (requires `~/.kaggle/kaggle.json` or `KAGGLE_USERNAME`/`KAGGLE_KEY`); clear error message if credentials are missing.
- `data/README.md` → data cards: source, URL, license, rows/columns, date fetched, caveats, checksum of the raw file.
- `data/eval/.gitkeep` and `.gitignore` entries for `data/raw/`, `data/processed/`.
- `scripts/seed_policyholders.py`: sample 50 rows from freMTPL2freq → `data/processed/seed_policyholders.csv` (driver age, vehicle age/power, bonus-malus, region) with deterministic seed.
- `pyproject.toml` at repo root (uv or pip-tools; Python 3.12) with a `data` extra.

**Tests:** unit tests for text extraction (fixture: first 2 pages of AKB saved as a tiny PDF) and for the seed sampler; fetch functions are tested with mocked HTTP.

**Done when:** `python scripts/fetch_data.py all` succeeds on a clean machine given a Kaggle token, and skips Kaggle with a helpful message without one.

**Risks:** GDV URL changes (keep the Musterbedingungen page URL as fallback and fail loudly); Kaggle terms require the user's own account — never commit the CSV.
