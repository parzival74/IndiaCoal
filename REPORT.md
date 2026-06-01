# Why efficiency explains only ~30% of PLF in India's subcritical coal fleet

**Dataset:** CSE analysis of CEA's CO₂ database, **2022-23, version 19** —
*Table 1: Performance of Subcritical units* (455 units).
**Two scope notes that drive several conclusions:** (1) the table is
**subcritical units only** — India's supercritical / ultra-supercritical (USC)
plants are *not* in it; (2) the vintage is **2022-23**, not 2024.

All numbers below are reproducible via `analysis/run_all.py`; raw outputs are in
`outputs/`.

---

## 0. The reported statistics — confirmed

| Set | Pearson r | R² | n |
|---|---|---|---|
| All units, Efficiency vs PLF | 0.475 | **22.6%** | 455 |
| PLF ≥ 20 only | **0.552** | **30.5%** | 438 |

Both match the figures in the brief exactly (17 units sit below 20% PLF). So the
factual premise is sound. The interpretation needs three corrections.

---

## 1. The core issue: efficiency is the wrong axis for merit order

Merit order dispatches on **lowest variable cost (₹/kWh)**, not thermal
efficiency:

```
variable cost ≈ SHR (kcal/kWh) × coal price (₹/Gcal) + secondary oil + variable O&M
```

Efficiency captures only the `SHR` term. **Coal price is the dominant term and it
is not in the dataset.** Indian thermal fuel cost ranges ~₹1.5/kWh (mine-mouth
lignite, pithead linkage coal) to ~₹4–5/kWh (imported coal). Two units at the
same efficiency can sit at opposite ends of the merit stack. So a *low* Eff↔PLF
correlation is **largely expected** and is **not** strong evidence that India
ignores merit order.

The data shows the mechanism directly (`outputs/02_variable_cost.txt`):

| Inferred coal source | n | Efficiency | Modelled VC (₹/kWh) | PLF | CO₂ (t/MWh) |
|---|---|---|---|---|---|
| Lignite | 34 | **27.3%** (worst) | **1.80** (cheapest) | 56.8% | **1.34** (dirtiest) |
| Domestic coal | 402 | 31.5% | 2.54 | 62.4% | 1.05 |
| Imported coal | 19 | **33.2%** (best) | **4.65** (dearest) | **26.6%** (idle) | **0.94** (cleanest) |

The starkest single case: **Mundra (Adani, imported coal) — 35.4% efficiency,
among the most efficient units in the fleet — runs at just 10–12% PLF**, while
**Neyveli lignite at 28.9% efficiency runs at ~83%**. That isn't merit order
failing; it's merit order *working on cost*. The efficient unit is idle because
imported coal is expensive; the inefficient unit runs flat-out because lignite is
mine-mouth and dirt cheap.

> **Statistical footnote — reverse causality.** Part of the 30% is *PLF → efficiency*,
> not *efficiency → PLF*: running a unit at low PLF means part-load operation off
> its design point, which *worsens* the measured heat rate. So the true causal
> effect of efficiency on dispatch is even weaker than 30%.

---

## 2. So what explains the other ~70%?

A multivariate OLS of PLF on **every usable plant-technical variable**
(`outputs/01_correlations.txt`, PLF ≥ 20, n = 438):

| Model | R² |
|---|---|
| Efficiency only | 30.5% |
| + Age + Capacity + GCV | 32.4% |
| + Sector | 38.1% |
| + Auxiliary consumption | **43.6%** |

**Everything measurable about the plant, combined, still leaves ~56%
unexplained.** That residual is dominated by variables *not in the spreadsheet*:
**coal cost / source, PPA structure & must-run status, RE backing-down, and
transmission / grid-node location.** Two measurable points stand out:

- **Sector is the single biggest jump (+5.7 pp of R²).** Central units run far
  hotter than the rest:

  | Sector | n | Mean PLF | Mean Eff | Mean Age |
  |---|---|---|---|---|
  | **Centre** (NTPC/DVC/NLC) | 130 | **71.1%** | 32.4 | 22.7 |
  | State | 187 | 58.8% | 30.2 | 24.2 |
  | Private | 121 | 58.4% | 31.6 | 13.8 |

  Central plants combine cheap linkage coal, firm long-term PPAs, payment
  security, and ISGS must-run status.

- **Auxiliary consumption** adds another ~5 pp — high-aux (older, inefficient)
  units run less.

---

## 3. The three hypotheses, tested against the data

### H1 — small/old Western plants ramp fast for the solar-drop / evening peak
**Largely contradicted in this data, but ultimately untestable here.**
- **Age has ~zero correlation with PLF (r = −0.015)** — old plants do *not* run
  more. **Bigger** plants run more, not smaller (Capacity r = +0.225; the 400+ MW
  band averages 68% PLF).
- **But annual PLF is a volume metric, not a flexibility metric.** Two-shifting
  and fast ramping show up as *cycling frequency and ramp rate*, which annual PLF
  averages away. So the flexibility intuition could still be true — it is just
  invisible in this dataset. Testing it needs block-level dispatch data
  (extension #3, `05_flexibility_framework.py`).

### H2 — proximity to load centres matters electrically
**Plausible, part of the residual, not testable here — and the coarse regional
proxy points more to *coal* proximity than *load* proximity.** Using a
company-derived grid region for the ~60% of units that are state utilities
(`outputs/03_regions.txt`):

| Region | n | Mean PLF |
|---|---|---|
| **Eastern** (coal belt: DVC/WBPDC/Jharkhand/Odisha) | 54 | **69.8%** |
| Southern | 68 | 58.5% |
| Western (Maharashtra/Gujarat) | 82 | 57.6% |
| Northern | 65 | 55.4% |

Eastern coal-belt states run hottest — a **cheap-pithead-coal (supply-side)**
signal, consistent with cost merit order, rather than the load-proximity story.
True proximity testing needs nodal / load-pocket / RLDC-bus data.

### H3 — DISCOMs prioritise their own plants to delay payments
**The aggregate points the opposite way.** If DISCOMs favoured their own state
gencos, state PLF would be *high* — but **state plants run the *least* (58.8% vs
71.1% central)**. The cash-flow logic is real in specific states/seasons (sunk
fixed-cost PPAs make running "free" at the margin), but it's confounded: central
plants are also genuinely cheaper and must-run, so they top the merit order
anyway. This dataset cannot isolate the effect.

---

## 4. "India maxes at 41% vs China's 50%" — apples to oranges

Three corrections; the gap shrinks substantially.

1. **This table is *subcritical only*.** Subcritical steam is thermodynamically
   capped at ~33–37% gross. The fleet here sits at a median 31.8% (99th pct
   35.5%); the lone 41.7% (Torangallu, imported coal) is an outlier. **India's
   supercritical and USC plants — the efficient ones — simply aren't in this
   table.**
2. **China's "≈50%" is one record unit, not its fleet.** [Pingshan Phase II hits
   49.37% net](https://www.powermag.com/chinas-pingshan-phase-ii-sets-new-bar-as-worlds-most-efficient-coal-power-plant/);
   China's **fleet average is ~38.6%**, USC units 44–46%, USC ~29% of capacity.
   The real story is build-out: China deployed massive USC capacity (2006–2020)
   while India still carries a large subcritical base.
3. **Measurement basis inflates China's number.** China reports **LHV (net)**;
   CSE's efficiency here is **GCV/HHV-based** (it's just 860 ÷ SHR). For India's
   sub-bituminous, high-ash coal, [converting HHV → LHV adds ~3 percentage
   points](https://www.gem.wiki/Estimating_carbon_dioxide_emissions_from_coal_plants).

A fair comparison is roughly **India's best USC (~40–42% net) vs China's best USC
(~47–49%)**, and **India subcritical fleet ~34% LHV vs China fleet ~38.6% LHV** —
a real but much smaller and more explainable gap than "41 vs 50."

---

## 5. The IPCC / CO₂-timing question

The skepticism is half right: **nobody has audited Indian coal-consumption data
within weeks of year-end — but the IPCC isn't who publishes the fast numbers.**

- **The IPCC does not produce annual country emission estimates.** It publishes
  *methodology* (2006 Guidelines + 2019 Refinement: emissions = activity data ×
  emission factor) and assessment reports every ~7 years.
- The **fast annual figures** come from the **Global Carbon Project**,
  **[Carbon Monitor](https://www.nature.com/articles/s41597-020-00708-7)**,
  **IEA**, **EDGAR**, and the **Energy Institute Statistical Review** — explicitly
  **preliminary nowcasts**, not inventories.
- **How they're produced so fast:** not from audited consumption, but from
  **high-frequency proxies** — daily/hourly power-generation data, monthly
  industrial-production indices, mobility, etc. For India, monthly **CEA
  generation**, **Coal India production**, and **customs import** statistics
  arrive with ~1-month lag, and consumption ≈ production + imports − stock change.
  IPCC Tier-1 emission factors (stable to ~2% YoY for coal) are applied,
  uncertainty bands attached, and figures revised later.
- The **official, audited** Indian numbers come via the **UNFCCC inventory**
  (Biennial Update Reports / National Communications) and lag **2–4 years**.

So both are true: the precise number is slow; the *estimate* is fast and
proxy-based.

---

## 6. The key correction: more money ≠ more CO₂

The brief assumed that not following merit order means *both* more cost *and* more
CO₂. In this fleet **those two objectives diverge.** The re-dispatch counterfactual
(`04_redispatch.py`; same total 763 TWh re-stacked; VC & EF held fixed; transmission
/ must-run / ramping ignored — a stylised model to size the trade-off):

| Scenario | Fuel cost (₹ cr) | CO₂ (MT) |
|---|---|---|
| 1. Actual (as-run) | 188,599 | 777.9 |
| 2. Cost-merit (cheapest VC first) | **180,252** | 764.9 |
| 3. Carbon-merit (cleanest first) | 194,808 | **746.0** |

Two findings:

- **The as-run dispatch is only ~4.4% above cost-optimal.** That is actually
  *evidence India broadly does follow merit order* — the low Eff↔PLF correlation
  was misleading because efficiency ≠ cost.
- **Cost-optimal and carbon-optimal are different objectives.** Going for least
  *cost* instead of least *carbon* costs **+18.9 MT of extra CO₂ to save ~₹14,556
  cr** — an implied abatement cost of roughly **₹7,700/tonne CO₂ (~$90/t)**. The
  cheapest power (pithead lignite, domestic coal) is among the dirtiest; the
  cleanest (imported coal) is the dearest, so strict economic merit order *raises*
  CO₂ relative to a carbon-ranked dispatch.

> Magnitudes scale with the fuel-price assumptions in `02_variable_cost.py`; the
> *direction* (cost and carbon optima diverge) is robust to them.

**This misalignment — India's cheapest coal power is also its dirtiest — is the
most policy-relevant finding here, and the textbook case for a carbon price to
re-align the cost and carbon merit orders.**

---

## 7. Can the variable-cost column be populated? (direct answer)

**Partially.** SHR is per-plant and real, but the dominant term — per-plant coal
price — is not in the file. `02_variable_cost.py` builds a **transparent,
category-level estimate** by inferring coal source (domestic/imported/lignite)
and applying documented price benchmarks. It is directionally correct (imported ⇒
expensive ⇒ idle) **but not plant-accurate**, and a flat per-category price
actually tracks PLF *worse* than efficiency (R² ≈ 14% vs 31%) because:
1. ~90% of units share one "domestic" price, so within that bucket the cost is
   just a rescaling of SHR;
2. the real merit-order dispersion lives *inside* the domestic fleet
   (pithead-distance, grade, e-auction share, freight), which a flat price can't
   reproduce;
3. GCV alone mislabels plants (Mundra's as-fired GCV ~4090 is below the import
   threshold — we fix it with a small curated importer list).

**To make it accurate, join plant-level Energy Charge Rate (ECR)** from CERC/SERC
tariff orders or Grid-India merit-order-despatch sheets. The code is structured to
accept that as a drop-in replacement. Full detail in
[`docs/methodology_variable_cost.md`](docs/methodology_variable_cost.md).

---

## 8. Extensions delivered & their data limits

| # | Extension | Status | Blocking data (not in file) |
|---|---|---|---|
| 1 | Variable cost (₹/kWh) | Modelled estimate | Plant-level ECR / coal price |
| 2 | Grid-region / load proximity | Coarse proxy (~60% coverage) | Lat/long, RLDC bus, load-pocket, congestion |
| 3 | Flexibility / ramp (H1) | Framework + synthetic demo | Block-level SCED generation |
| 4 | Cost-vs-carbon re-dispatch | Done (stylised) | Transmission/must-run limits for realism |

See [`docs/data_sources.md`](docs/data_sources.md) for exactly where to obtain the
missing inputs. (The remote environment blocks Grid-India/CEA, so live SCED data
could not be fetched in-session.)

---

### Sources
- [POWER — Pingshan Phase II (49.37% net)](https://www.powermag.com/chinas-pingshan-phase-ii-sets-new-bar-as-worlds-most-efficient-coal-power-plant/)
- [POWER — world's most efficient coal fleets](https://www.powermag.com/who-has-the-worlds-most-efficient-coal-power-plant-fleet/)
- [Global Energy Monitor — estimating CO₂ from coal plants (HHV→LHV conversion)](https://www.gem.wiki/Estimating_carbon_dioxide_emissions_from_coal_plants)
- [Carbon Monitor — near-real-time daily CO₂ (Nature Sci. Data)](https://www.nature.com/articles/s41597-020-00708-7)
