# CLAUDE.md — project memory for IndiaCoal

Read this first. It carries everything needed to continue the work without prior
chat context. Active branch: **`claude/keen-newton-P0cFA`** (open as **PR #1**).
The kickoff prompt for the current task is in
[`docs/NEXT_SESSION_PROMPT.md`](docs/NEXT_SESSION_PROMPT.md); a queued sub-analysis
(does efficiency≈cost at pithead plants?) is in
[`docs/PITHEAD_TEST_PROMPT.md`](docs/PITHEAD_TEST_PROMPT.md).

## What this project is
Analysis of why thermal **efficiency explains only ~30% of plant load factor
(PLF)** in India's coal fleet, using a CSE/CEA dataset, plus a reproducible
pipeline and several extensions. The headline question: are we failing to follow
merit order, and what would that cost in money and CO₂?

## The data — and two caveats that matter
- Source: `data/raw/CSE_subcritical_coal_plants_CEA_2022-23.xlsx` — CSE's analysis
  of **CEA's CO₂ database, 2022-23 v19**, *Table 1: Performance of Subcritical units*.
- **Caveat 1: SUBCRITICAL units only.** India's supercritical / ultra-supercritical
  (USC) plants — the efficient ones — are NOT in this table. This is why the
  "India 41% vs China 50%" comparison is apples-to-oranges (subcritical vs USC).
- **Caveat 2: vintage is 2022-23, not 2024**, despite the original filename.
- 455 usable units. Fields: name, company, sector (Centre/State/Private), age,
  GCV, fuel (Coal/Lignite), capacity, emission factor, PLF, SHR, efficiency, aux
  consumption, net generation, CO₂.

## Key findings (don't re-derive from scratch; verify via the pipeline)
- Reproduced: Eff↔PLF **R²=22.6%** (all), **r=0.552 / R²=30.5%** (PLF≥20).
- **Efficiency is the wrong axis for merit order**, which dispatches on *variable
  cost* (₹/kWh). Coal price (not in the file) dominates. Imported-coal plants
  (e.g. Mundra, 35% eff) sit idle at ~10% PLF; cheap pithead lignite (29% eff)
  runs at ~83%. The low R² is largely expected, NOT proof merit order is ignored.
- Every measurable plant variable combined explains only **~44%** of PLF.
  **Sector** is the biggest categorical driver: Centre **71%** vs State/Private
  **~58%** PLF. Age has **~0** correlation; bigger plants run *more*.
- Hypotheses: H1 (old/small plants ramp) — undercut (age r≈0) and untestable on
  annual PLF; H2 (load proximity) — region looks coal-proximity driven, needs
  nodal data; H3 (DISCOMs favour own plants) — aggregate runs opposite (state
  plants run least).
- **Re-dispatch counterfactual** (on the real-CIL-grounded cost): as-run dispatch is
  only **~5.5% above cost-optimal** (merit order broadly IS followed). Cost-optimal vs
  carbon-optimal **diverge by ~21 MT CO₂ for ~₹15,300 cr** (implied ~₹7,200/t). So
  "no merit order ⇒ more money AND more CO₂" is wrong — the cheapest coal power
  is also the dirtiest; the two objectives diverge.
- **Domestic coal price is now REAL** (FY2022-23): CIL grade-wise pithead notified
  prices (notif. 194 dated 27-11-2020, in force all of FY2022-23) + published levies
  + flagged flat freight → domestic ≈ ₹2.1/kWh (was a ₹850/Gcal *assumed* anchor).
- **CERC per-station ECR is 2018-19 basis** (working-capital ECR on Oct–Dec 2018 coal
  cost), so it's a **labelled cross-check** (`08`), not the FY2022-23 headline. It
  reveals the real central-station spread ₹1.25→₹3.48/kWh that the flat-freight model
  compresses to ₹1.83–2.08 — i.e. per-plant freight/pithead-distance is the missing axis.
- IPCC does NOT publish fast annual country CO₂; Global Carbon Project / Carbon
  Monitor / IEA do, via high-frequency proxies (nowcasts), revised later.

## Repo layout
```
REPORT.md            the analysis write-up (main deliverable)
README.md            quick start + pipeline table
CLAUDE.md            this file
requirements.txt     pandas, numpy, scipy, openpyxl
data/raw/            source xlsx; cil_grade_prices_fy2022-23.csv (REAL); plant_ecr_cerc_2018basis.csv (REAL, cross-check); plant_ecr_template.csv; (drop plant_ecr.csv + sced_blocks.csv here)
data/                cse_subcritical_clean.csv, plant_cost_blended.csv  (generated)
analysis/            common.py + numbered pipeline scripts (01–08) + run_all.py
outputs/             *.txt results (committed)
docs/                methodology_variable_cost.md, data_sources.md
.claude/             SessionStart hook (installs deps + runs pipeline on web)
```

## How to run
```bash
pip install -r requirements.txt
python3 analysis/run_all.py      # runs common → 01 → 02 → 03 → 04 → 05 → 06
```
Pipeline scripts:
- `common.py` — clean xlsx → CSV; tags each plant with official Coal India GCV
  grade (G1–G17, real slabs).
- `01_correlations.py` — reproduces stats + multivariate PLF model.
- `02_variable_cost.py` — variable cost ₹/kWh. **Domestic price is REAL**: CIL
  FY2022-23 grade-wise pithead notified price (`data/raw/cil_grade_prices_fy2022-23.csv`)
  + statutory levies + flagged flat freight. Lignite/imported keep modelled anchors.
- `03_regions.py` — grid-region proxy for H2 (~60% coverage, state utilities).
- `04_redispatch.py` — cost-vs-carbon counterfactual on modelled cost.
- `05_flexibility_framework.py` — H1 ramp/cycling metrics framework (needs
  block-level SCED at `data/raw/sced_blocks.csv`; runs on synthetic demo otherwise).
- `06_apply_ecr.py` — FY2022-23 **metered** per-station ECR override from
  `data/raw/plant_ecr.csv` (currently empty: feeds down → 0% coverage; headline =
  real-CIL model). Fuzzy-matches names, reports coverage, re-runs the counterfactual.
- `07_fetch_ecr.py` — **fetches real data** from cercind.gov.in: CIL grade prices
  (→02) + CERC per-station ECR (→08, 2018-basis); probes the FY2022-23 feeds (down).
  Needs network + pdfplumber/pypdfium2. Not in run_all (committed CSVs make it offline).
- `08_cerc_crosscheck.py` — CERC per-station ECR (2018-19 basis) vs the FY2022-23
  model, clearly labelled; 14 central stations; NOT the headline counterfactual.

## CURRENT TASK — status (2026-06 Full-access session)
Goal: replace modelled coal prices with real published data, FY2022-23 vintage.

**DONE this session** (both layers, as agreed):
- **Domestic coal price → REAL.** Fetched CIL FY2022-23 grade-wise pithead notified
  prices from cercind.gov.in's CPI archive (notif. 194 dated 27-11-2020, in force all
  of FY2022-23) → `data/raw/cil_grade_prices_fy2022-23.csv`; `02` now prices domestic
  coal on it + statutory levies (royalty 14%, GST 5%, cess ₹400/t) + a flagged flat
  freight (₹900/t). Replaces the old assumed ₹850/Gcal anchor.
- **CERC per-station ECR → cross-check (2018-basis).** Parsed 26 CERC 2019-24
  generation-tariff orders → ECR for **14 central stations** → `data/raw/plant_ecr_cerc_2018basis.csv`;
  surfaced by `08_cerc_crosscheck.py`. **Kept OUT of the FY2022-23 headline** because
  CERC's ECR is computed on Oct–Dec 2018 coal cost (2018-19 basis) — vintage rule.
  Explicit curated name aliases (a difflib match wrongly hit "Bhadradri" for Dadri).

**KEY FINDING / why not 100%:** the genuinely FY2022-23 **metered** per-station ECR
feeds — **Grid-India SCED, POSOCO eLibrary, state SLDC stacks, MERIT/NPP — all returned
HTTP 503 / refused** this session (cercind.gov.in and coal.gov.in were 200). So the
FY2022-23 per-station override (`06`, `data/raw/plant_ecr.csv`) has **0% real coverage**
and the headline cost rests on the real-CIL-grounded model. We refuse to fabricate it.

**REMAINING (next session, when those feeds are up):**
1. Verify: `curl -s -o /dev/null -w '%{http_code}' https://grid-india.in` → 200.
2. Implement the SCED/SLDC/MERIT parser in `07_fetch_ecr.py` (it refuses fake data).
3. `python3 analysis/07_fetch_ecr.py` → writes `data/raw/plant_ecr.csv` (FY2022-23 only).
4. `python3 analysis/06_apply_ecr.py` → real-coverage override + counterfactual.
5. Update REPORT.md §7 coverage; commit; push to the working branch.

## Working conventions
- **Honesty over polish:** never fabricate data. Label modelled vs real clearly
  (the `vc_source` column / coverage reports do this). Keep scaffolds inert until
  real data backs them.
- Develop on `claude/keen-newton-P0cFA`; push there (PR #1). Don't push elsewhere
  without explicit permission. Don't open new PRs unless asked.
- Outputs are deterministic — regenerating them produces no git diff.
- Do not put model identifiers in committed artifacts.
- The repo started empty; `main` is an empty base branch created for PR #1.
