# Data cards

Downloaded by `python scripts/fetch_data.py all` (see `docs/DATA.md` for why each source was chosen).
`data/raw/` and `data/processed/` are git-ignored; `data/processed/manifest.json` records the checksum,
size, row/column counts and fetch time of every file on your machine. `data/eval/` holds small
hand-written evaluation sets and is committed.

| Card | Source | License | Size | Fetched | Used in |
|---|---|---|---|---|---|
| [GDV AKB 2015](#gdv-akb-2015) | GDV Musterbedingungen | public reference text | 55 pages / 21,059 words | 2026-10-27 | RAG corpus (task 3) |
| [freMTPL2freq](#fremtpl2freq) | OpenML 41214 | CC0 | 678,013 × 12 | 2026-10-27 | seed policyholders (task 1), severity stretch (task 8) |
| [freMTPL2sev](#fremtpl2sev) | OpenML 41215 | CC0 | 26,639 × 2 | 2026-10-27 | severity stretch (task 8) |
| [Vehicle Insurance Fraud](#vehicle-insurance-fraud-detection) | Kaggle `khusheekapoor/vehicle-insurance-fraud-detection` | CC0 (as shown on Kaggle) | 15,420 × 33 | needs your Kaggle token | fraud model (task 2) |

## GDV AKB 2015

- **What:** *Allgemeine Bedingungen für die Kfz-Versicherung (AKB 2015)* — the German Insurance Association's model motor insurance conditions; numbered clauses A.1 (Haftpflicht) … G (Laufzeit/Kündigung).
- **URL:** https://www.gdv.de/resource/blob/6178/dd2bfe79d9d75902e4cc24b5560af6ed/01-allgemeine-bedingungen-fuer-die-kfz-versicherung-akb-2015--data.pdf (listed at https://www.gdv.de/gdv/service/musterbedingungen; the script falls back to that page if the direct link moves).
- **Files:** `data/raw/gdv/akb_2015.pdf` (326,497 bytes), `data/processed/akb_2015.txt` (pages separated by `\f`).
- **Checksum (sha256, PDF):** `e958df780490f4e014da387d34b9944e94b67d856aa781c658aa2a4baddd1a96`
- **Caveats:** unbinding model wording — real policies deviate; the agent must say "according to the AKB 2015 model terms". Text extraction keeps the clause numbering but loses table layout; the RAG chunker (task 3) works on clause ids, not pages. `pypdf` reports a "Stand" date that is the PDF's generation stamp, not the wording version.
- **Test fixture:** `tests/fixtures/akb_2015_first2pages.pdf` (first two pages, 9.5 KB).

## freMTPL2freq

- **What:** French motor third-party-liability policies, one year of exposure each, from CASdatasets (Charpentier, *Computational Actuarial Science with R*).
- **URL:** https://www.openml.org/d/41214 — License CC0, no login.
- **File:** `data/processed/freMTPL2freq.parquet` — 678,013 rows × 12 columns: `IDpol, ClaimNb, Exposure, Area, VehPower, VehAge, DrivAge, BonusMalus, VehBrand, VehGas, Density, Region`.
- **Checksum (sha256, parquet):** `3e93d52b136941e890c3ef7010fdc59fe1be23ea9462ea9bb39746d0df475d55` (parquet written by pyarrow; may differ across pyarrow versions — compare row counts if it does).
- **Caveats:** OpenML's copy has 678,013 rows (the R package documents 677,991); `ClaimNb` has a handful of implausible values (>4) that actuarial papers cap. French regions (`R11` = Île-de-France …), not German ones — the seed layer only uses them as realistic distributions, the demo persona is German.
- **Derived:** `data/processed/seed_policyholders.csv` — 50 rows, `Exposure ≥ 0.5`, driver age 18–85, `random_state=42`, sorted by `IDpol`. Regenerate with `python scripts/seed_policyholders.py`.

## freMTPL2sev

- **What:** claim amounts for the policies above (`IDpol, ClaimAmount`).
- **URL:** https://www.openml.org/d/41215 — License CC0, no login.
- **File:** `data/processed/freMTPL2sev.parquet` — 26,639 rows × 2 columns.
- **Checksum (sha256, parquet):** `f860f391acfa4ea6cb891cd12417ae8dcb4bb5ca398d7cd65e9835e4a9910399`
- **Caveats:** heavy right tail (a few claims above 1 M€); only used for the optional severity model.

## Vehicle Insurance Fraud Detection

- **What:** 15,420 US automobile claims from 1994–1996 (the Oracle "carclaims" data), 923 labelled fraudulent (`FraudFound_P`, ~6 %). 33 mostly categorical/binned columns.
- **URL:** https://www.kaggle.com/datasets/khusheekapoor/vehicle-insurance-fraud-detection — License shown as CC0. Requires a Kaggle account and API token (`~/.kaggle/kaggle.json` or `KAGGLE_USERNAME`/`KAGGLE_KEY`); `fetch_data.py` prints instructions and skips this source if neither is present.
- **File:** `data/raw/kaggle/fraud_oracle.csv`. Checksum is written to `manifest.json` after download; it is not recorded here because the file is fetched under your own Kaggle account.
- **Caveats:** 1990s US data with binned features (`VehiclePrice` is a range, `AgeOfVehicle` a bucket). `Sex`, `MaritalStatus`, `Age`, `AgeOfPolicyHolder`, `PolicyNumber`, `RepNumber` are excluded from modelling (fairness / leakage) — see the model card in task 2. The dataset's own documentation is thin; treat column semantics as inferred.

## Not downloaded by the script

- **InsuranceQA** (GitHub `shuzi/insuranceQA`, HF `deccan-ai/insuranceQA-v2`) — pulled ad hoc in task 3 for retriever sanity checks; license unclear, research use only.
- **Car damage images** — stretch (task 8); choose a set with an explicit license first.
