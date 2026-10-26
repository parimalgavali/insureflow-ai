# Data

All sources are public. Nothing large is committed; `scripts/fetch_data.py` (task 1) downloads into `data/raw/` (git-ignored). Licenses are those of the sources; check them before redistributing derived files.

## Sources

### 1. GDV AKB 2015 — model motor insurance terms (RAG corpus)

- **What:** *Allgemeine Bedingungen für die Kfz-Versicherung (AKB 2015)*, the German Insurance Association's (GDV) unbinding model conditions that most German motor policies are based on. 55 pages, ~21,000 words, numbered clauses (A.1 Haftpflicht, A.2 Kasko incl. Teil-/Vollkasko, A.3 Schutzbrief, A.4 Fahrerschutz, B Beginn, C Beitrag, D Pflichten bei Gebrauch, E Pflichten im Schadenfall, F Rechte und Pflichten der mitversicherten Personen, G Laufzeit/Kündigung, …).
- **Where:** https://www.gdv.de/gdv/service/musterbedingungen → "01 Allgemeine Bedingungen für die Kfz-Versicherung (AKB 2015)". The same page lists ~77 other Musterbedingungen (Hausrat VHB, Haftpflicht AHB, Rechtsschutz ARB …) if the project is ever extended beyond motor.
- **Verified:** 2026-10-27, PDF downloads (326 KB) and `pypdf` extracts text cleanly including the clause table of contents.
- **Terms:** published for public reference by the GDV; we store the download URL and a fetch script, not the PDF itself, and cite clauses rather than reproducing long passages in the UI.
- **Used for:** chunking by clause → embeddings → pgvector → retrieval with citations (task 3).

### 2. Vehicle Insurance Fraud Detection (fraud model)

- **What:** 15,420 real US automobile claims from 1994–1996 (the Oracle "carclaims" dataset), 923 labelled fraudulent (~6%). 33 columns, e.g. `Month, DayOfWeek, Make, AccidentArea, Sex, MaritalStatus, Age, Fault, PolicyType, VehicleCategory, VehiclePrice, Deductible, DriverRating, Days_Policy_Accident, Days_Policy_Claim, PastNumberOfClaims, AgeOfVehicle, AgeOfPolicyHolder, PoliceReportFiled, WitnessPresent, AgentType, NumberOfSuppliments, AddressChange_Claim, NumberOfCars, BasePolicy, FraudFound_P`.
- **Where:** Kaggle `khusheekapoor/vehicle-insurance-fraud-detection` (`fraud_oracle.csv`). License shown on Kaggle: CC0.
- **Access:** requires a Kaggle account + API token (`~/.kaggle/kaggle.json`). The fetch script uses the `kaggle` CLI.
- **Known caveats:** 1990s US data; categorical bins rather than raw numbers; features like `Sex`, `MaritalStatus`, `Age` must be **excluded** from the model (fairness) — this is a stated modelling decision in the model card.
- **Used for:** gradient-boosting fraud-risk model with imbalanced-classification metrics and per-prediction feature contributions (task 2).

### 3. freMTPL2freq / freMTPL2sev (realistic seed data, optional severity model)

- **What:** 677,991 real French motor third-party-liability policies (one year of exposure) with `Exposure, Area, VehPower, VehAge, DrivAge, BonusMalus, VehBrand, VehGas, Density, Region, ClaimNb`; plus 26,639 claim amounts (`freMTPL2sev`). From CASdatasets (Charpentier, *Computational Actuarial Science with R*).
- **Where:** OpenML dataset IDs 41214 and 41215. License CC0. No login required (`openml` Python package or direct ARFF/CSV download).
- **Verified:** 2026-10-27 via the OpenML API.
- **Used for:** sampling realistic demo policyholders (driver age, vehicle age/power, bonus-malus, region) for the seed layer; stretch: claim-frequency/severity model (task 8).

### 4. InsuranceQA (RAG evaluation / FAQ fallback)

- **What:** ~12k real consumer insurance questions with answers written by licensed agents (insurancelibrary.com), English. From Feng et al., ASRU 2015.
- **Where:** GitHub `shuzi/insuranceQA` (tokenised original); Hugging Face `deccan-ai/insuranceQA-v2` (detokenised). License not stated on HF; research use.
- **Used for:** sanity-checking the retriever on general insurance questions and sourcing phrasing for evaluation questions. The primary RAG eval set is hand-written against AKB clauses (task 3).

### 5. Car damage images (stretch only)

- Several Hugging Face sets (`DrBimmer/comprehensive-car-damage`, `riddhi114/car-damage-dataset-with-yolov8`, `gigwegbe/damaged-car-dataset-annotated`, …). Licenses are mostly unstated — **pick one with an explicit license before training** (task 8).

### Rejected

- Kaggle `buntyshah/auto-insurance-claims-data` — 1,000 rows, appears synthetic.
- RISC / RISCBAC — well-made but synthetic bilingual (FR/EN) Quebec contracts; we have a real German wording instead.
- v1's `synthetic-data-generator` — retired; see `legacy/`.

## How the sources fit together

There is no public dataset that links claim narratives, policy wording and fraud labels. v2 joins three real sources through a thin **seed layer**:

```
seed policyholders (sampled from freMTPL2)  ──┐
   + a product definition (Haftpflicht / Teilkasko / Vollkasko, deductible)
                                                ├──► demo claim conversation
AKB clauses (RAG)  ─────────────────────────────┤
fraud model trained on Kaggle claims  ──────────┘
```

The fraud model's input features are mapped from the conversation (e.g. days between accident and report, police report filed, witness present, prior claims, vehicle age) to the Kaggle schema. The mapping is documented in the model card and is deliberately conservative: the score is a *signal with reasons*, never a decision.

## Local layout

```
data/
  raw/        downloaded originals (git-ignored)
  processed/  cleaned parquet/CSV produced by scripts (git-ignored)
  eval/       small hand-written evaluation sets (committed)
```
