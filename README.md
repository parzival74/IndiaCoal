# IndiaCoal — subcritical fleet efficiency vs dispatch analysis

Analysis of the CSE/CEA dataset of India's **subcritical** coal units
(CEA CO₂ database, 2022-23 v19), investigating why thermal efficiency explains
only ~30% of plant load factor (PLF), and what explains the rest.

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
| `02_variable_cost.py` | **Ext #1** modelled variable cost (₹/kWh) | done (modelled) |
| `03_regions.py` | **Ext #2** grid-region proxy for "load proximity" | done (~60% coverage) |
| `04_redispatch.py` | **Ext #4** cost vs carbon re-dispatch counterfactual | done (stylised) |
| `05_flexibility_framework.py` | **Ext #3** ramp/cycling metrics for H1 | framework (needs SCED data) |

Extensions #1–#3 are limited by data **not present in the source file**; see
[`docs/data_sources.md`](docs/data_sources.md) for exactly what to add.
