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
- **Re-dispatch counterfactual**: as-run dispatch is only **~4.4% above
  cost-optimal** (merit order broadly IS followed). Cost-optimal vs carbon-optimal
  **diverge by ~19–20 MT CO₂ for ~₹14,500–15,000 cr** (implied ~₹7,700/t). So
  "no merit order ⇒ more money AND more CO₂" is wrong — the cheapest coal power
  is also the dirtiest; the two objectives diverge.
- IPCC does NOT publish fast annual country CO₂; Global Carbon Project / Carbon
  Monitor / IEA do, via high-frequency proxies (nowcasts), revised later.

## Repo layout
```
REPORT.md            the analysis write-up (main deliverable)
README.md            quick start + pipeline table
CLAUDE.md            this file
requirements.txt     pandas, numpy, scipy, openpyxl
data/raw/            source xlsx; plant_ecr_template.csv; (drop plant_ecr.csv + sced_blocks.csv here)
data/                cse_subcritical_clean.csv, plant_cost_blended.csv  (generated)
analysis/            common.py + numbered pipeline scripts + run_all.py
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
- `02_variable_cost.py` — **modelled** variable cost ₹/kWh (grade-aware domestic
  price; imported/lignite anchors). The price block at top is the only assumption
  set; edit it or override with real ECR (see 06).
- `03_regions.py` — grid-region proxy for H2 (~60% coverage, state utilities).
- `04_redispatch.py` — cost-vs-carbon counterfactual on modelled cost.
- `05_flexibility_framework.py` — H1 ramp/cycling metrics framework (needs
  block-level SCED at `data/raw/sced_blocks.csv`; runs on synthetic demo otherwise).
- `06_apply_ecr.py` — overrides modelled cost with **real per-station ECR** from
  `data/raw/plant_ecr.csv`, fuzzy-matches names, reports coverage, re-runs the
  counterfactual on the blended cost. Currently 1 seeded real row (Talcher).
- `07_fetch_ecr.py` — **scaffold** to fetch real ECR (needs network; see below).

## CURRENT TASK: replace modelled prices with real plant-level ECR
The variable cost in `02` is a transparent MODEL. Real Energy Charge Rate (ECR)
is published and should override it. The seeded example proves why it matters:
the model priced **Talcher at ~₹2.7/kWh**, but its **real CERC ECR is ₹1.48/kWh**
(pithead) — the model can't infer pithead cheapness.

**Vintage rule:** the performance data is FY2022-23, so collect **FY2022-23 ECR
only** (coal prices swung hugely; don't mix vintages). **Sources, ranked** (detail
in `docs/data_sources.md` #1): (1) **CERC FY2022-23 tariff orders** `cercind.gov.in`
(regulated central/ISGS ECR; per-petition PDFs); (2) **Grid-India SCED statements**
`grid-india.in` / `hrd.posoco.in/elibrary` (per-generator variable cost, ISGS);
(3) **state SLDC daily merit-order stacks** (most granular, ~30 sites); (4) **Coal
India 2022-23 grade prices** `coal.gov.in` × SHR (universal fallback). MERIT
`meritindia.in` is an **interactive map** (dynamic XHR data, flaky) — last resort
only. Wayback is NOT used (didn't capture MERIT's dynamic data; dated docs are better).

**Network status:** these hosts were firewalled (HTTP 403) under the "Trusted"
policy in prior sessions. The environment is now set to **Full** access, which
applies only to NEW sessions. A fresh session must:
1. Verify: `curl -s -o /dev/null -w '%{http_code}' https://meritindia.in` → expect
   **200** (if 403, the session's environment isn't the Full-access one).
2. Complete the parser TODOs in `analysis/07_fetch_ecr.py` against the real
   responses (it refuses to emit fabricated data — keep it that way).
3. Run `python3 analysis/07_fetch_ecr.py` → writes `data/raw/plant_ecr.csv`.
4. Run `python3 analysis/06_apply_ecr.py` → real-coverage override + counterfactual.
5. Update REPORT.md coverage numbers, commit, push to `claude/keen-newton-P0cFA`.

## Working conventions
- **Honesty over polish:** never fabricate data. Label modelled vs real clearly
  (the `vc_source` column / coverage reports do this). Keep scaffolds inert until
  real data backs them.
- Develop on `claude/keen-newton-P0cFA`; push there (PR #1). Don't push elsewhere
  without explicit permission. Don't open new PRs unless asked.
- Outputs are deterministic — regenerating them produces no git diff.
- Do not put model identifiers in committed artifacts.
- The repo started empty; `main` is an empty base branch created for PR #1.
