# IndiaCoal — subcritical fleet efficiency vs dispatch analysis

Analysis of the CSE/CEA dataset of India's **subcritical** coal units
(CEA CO₂ database, 2022-23 v19), investigating why thermal efficiency explains
only ~30% of plant load factor (PLF), and what explains the rest.

**New session?** Read [`CLAUDE.md`](CLAUDE.md) first — it carries full context and
findings. Domestic coal cost is now grounded on **real Coal India FY2022-23 notified
prices**; the remaining task is FY2022-23 *metered* per-station ECR (feeds were down).

**Read [`REPORT.md`](REPORT.md) for the full write-up.**

## Layout
```
data/raw/   source workbook (+ drop sced_blocks.csv here for extension #3)
data/       cse_subcritical_clean.csv  (built; gains variable_cost + region columns)
analysis/   pipeline scripts (run in order, or via run_all.py)
outputs/    text results from each script
docs/       methodology + data-source notes
REPORT.md   the analysis
```

## Run
```bash
pip install -r requirements.txt
python3 analysis/run_all.py
```

## Pipeline
| Script | What | Status |
|---|---|---|
| `common.py` | clean the workbook → CSV | — |
| `01_correlations.py` | reproduce Eff↔PLF stats + multivariate PLF model | done |
| `02_variable_cost.py` | **Ext #1** variable cost (₹/kWh); domestic on **real CIL FY2022-23 prices** | done (real domestic price) |
| `03_regions.py` | **Ext #2** grid-region proxy for "load proximity" | done (~60% coverage) |
| `04_redispatch.py` | **Ext #4** cost vs carbon re-dispatch counterfactual | done (stylised) |
| `05_flexibility_framework.py` | **Ext #3** ramp/cycling metrics for H1 | framework (needs SCED data) |
| `06_apply_ecr.py` | apply **FY2022-23 metered per-station ECR** over the model | ready; 0% coverage (feeds down) |
| `07_fetch_ecr.py` | fetch CIL prices + CERC orders from source; probe ECR feeds | needs network (not in run_all) |
| `08_cerc_crosscheck.py` | **CERC per-station ECR cross-check** (2018-19 basis, labelled) | done (14 central stations) |
| `09_pithead_test.py` | side analysis: does efficiency tighten as a cost/PLF proxy at pithead plants? | done (PLF-side is a lignite artifact; cost-side see `10`) |
| `fetch_datagov_ecr.py` | fetch real per-station ECR from data.gov.in tariff statements (env-var key) | needs network + DATAGOVIN_API_KEY (not in run_all) |
| `10_datagov_ecr.py` | **contemporaneous central/ISGS ECR cross-check** (data.gov.in, 2021-23) | done (29 stations; r=0.99 vs CERC-2018) |

Extensions #1–#3 are limited by data **not present in the source file**; see
[`docs/data_sources.md`](docs/data_sources.md) for exactly what to add.
