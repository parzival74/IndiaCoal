# Methodology: the variable-cost column

## The question
*"Is it possible to populate the variable-cost column?"*

**Short answer: the dominant term (the domestic coal price) is now populated with
REAL, FY2022-23-vintage Coal India notified prices; the per-plant freight dispersion
that the merit order really turns on still needs metered per-station ECR, whose
feeds were unreachable this session. So: real and correctly-vintaged at the fuel-price
level, not yet plant-accurate at the freight/location level. See §"three layers".**

## Why merit order needs variable cost, not efficiency
Merit order dispatches the **lowest variable cost (₹/kWh)** first. For a coal unit:

```
variable_cost (₹/kWh) = SHR (kcal/kWh) × fuel_price (₹/Gcal) / 1e6
                        + non_fuel_variable (₹/kWh)
```

Efficiency only captures the `SHR` term. The **`fuel_price` term is the dominant
source of variation** and it is *not in the CSE/CEA file*. Indian thermal fuel
costs span roughly ₹1.5/kWh (mine-mouth lignite, pithead linkage coal) to
₹4–5/kWh (imported coal). Two units at identical efficiency can therefore sit at
opposite ends of the merit stack. That is why efficiency explains only ~30% of
PLF.

## What we can and cannot derive from the file
| Term | In the file? | How we handle it |
|---|---|---|
| SHR (kcal/kWh) | **Yes**, per unit | Used directly |
| Coal source (domestic/imported/lignite) | No | **Inferred** from fuel type, GCV, name, + a curated importer list |
| Fuel price (₹/Gcal), domestic | No (in file) | **REAL** — CIL FY2022-23 grade-wise pithead notified price + published levies (below) |
| Fuel price (₹/Gcal), lignite & imported | No | **Modelled** anchors (CIL price n/a: captive lignite / seaborne imports) |
| Pithead vs distant, linkage vs e-auction, washery, blend | No | **Not captured** — the main residual (CERC cross-check sizes it) |
| Non-fuel variable (oil + VOM) | No | Flat ₹0.20/kWh assumption |

## Three layers (what is real vs modelled)
**Layer (a) — domestic coal price: REAL, FY2022-23.** `02_variable_cost.py` prices
domestic coal from `data/raw/cil_grade_prices_fy2022-23.csv` — the Coal India
grade-wise **pithead** notified price (Power-Utilities column), from CIL notification
194 dated 27-11-2020, which was in force across all of FY2022-23 (CIL did not revise
non-coking prices again until 31-May-2023). Build-up to landed ₹/tonne:

```
landed = pithead_ROM(grade) × (1 + royalty 0.14 + GST 0.05)   # real statutory rates
         + GST compensation cess ₹400/t                        # real, FY2022-23
         + sizing/surface transport ₹150/t                     # CIL "other charges"
         + rail freight ₹900/t                                 # MODELLED, FLAGGED
₹/Gcal = landed × 1000 / GCV_plant                             # plant's real GCV
```

Everything except the last freight term is real and period-correct. Freight is flat
because **per-plant lead distance is not in the dataset** — and that flat term is
exactly what compresses the real pithead-vs-distant spread (see the cross-check).

**Layer (b) — lignite & imported: modelled anchors** (₹500 and ₹1700/Gcal). CIL's
notified price doesn't cover captive lignite (e.g. NLC) or seaborne imports, and no
real per-station FY2022-23 ECR could be fetched for them, so these stay labelled
modelled. Imported is inferred when the name contains "imp", **or** GCV > 4800
kcal/kg, **or** the plant is on `KNOWN_IMPORTED_KEYWORDS` (Mundra, Coastal Energen,
Udupi/UPCL, ITPCL, Essar …). Result: imported ≈ ₹4.6/kWh (idle, ~27% PLF), lignite
≈ ₹1.8/kWh, domestic ≈ ₹2.1/kWh.

**Layer (c) — CERC per-station ECR: REAL but 2018-19 basis → cross-check only**
(`08_cerc_crosscheck.py`, `data/raw/plant_ecr_cerc_2018basis.csv`). See below.

## The honest limitation
A flat freight term still makes the variable cost track PLF (r≈−0.43, R²≈18%)
somewhat *worse* than efficiency (R²≈31%). Reasons:
1. ~88% of units share the compressed domestic band, so within it the cost is largely
   a rescaling of SHR.
2. The real merit-order dispersion lives **inside** the domestic fleet
   (pithead-distance, freight, e-auction share, washery), which a flat freight term
   cannot reproduce — the **CERC cross-check** shows the real central-station ECR
   spans ₹1.25→₹3.48/kWh while the model compresses it to ₹1.83–2.08.
3. The GCV signal alone is unreliable — Mundra's as-fired GCV (~4090) is *below*
   the import threshold, so without the curated overlay it is mis-labelled domestic.

**Conclusion:** the domestic *price level* is now real and correctly vintaged; the
*within-fleet dispersion* (freight/location) still needs metered per-station ECR.

## The CERC cross-check (layer c), and why it isn't the headline
CERC tariff orders are reachable and we extracted the determined ECR for **14 central
stations** from the 2019-24 generation-tariff orders. **But CERC computes that ECR on
the Oct–Dec 2018 landed coal cost (a 2018-19 basis); the energy charge itself is
monthly actual pass-through, "subject to truing-up".** It is therefore *not* FY2022-23
data, so it is kept out of the FY2022-23 headline and used only by `08_cerc_crosscheck.py`.
Station names are mapped with an **explicit curated alias list** (a difflib fuzzy match
wrongly snapped "National Capital TPS (Dadri)" onto the unrelated "Bhadradri" plant —
the kind of error the cross-check is designed to avoid).

**Worked example:** an earlier hand-seeded row put Talcher at ₹1.48/kWh; the real CERC
determination figure for Talcher Stage-II is **₹1.85/kWh (2018-19 basis)** vs ₹1.98
modelled. Talcher is *pithead* — cheap because of zero rail freight, which the
GCV/source model and the flat freight term both miss. Only metered FY2022-23 per-station
ECR (layer d) supplies that.

## How to finish it — the FY2022-23 ECR override layer (`06_apply_ecr.py`)
The remaining gap is **FY2022-23 *metered* per-station ECR**, published by:
- **Grid-India SCED** statements / **POSOCO eLibrary** (interstate stations).
- **State SLDC** daily merit-order-despatch stacks (state gencos).
- **MERIT** (meritindia.in) — interactive, flaky; last resort.

**Workflow:** copy `data/raw/plant_ecr_template.csv` → `data/raw/plant_ecr.csv`, fill
it with FY2022-23 ECR (`match_name, ecr_rs_per_kwh, period, source`), and run
`python3 analysis/06_apply_ecr.py`. It fuzzy-matches station names, overrides the model
where real ECR exists (else falls back), tracks a `vc_source` flag and coverage, and
re-runs the counterfactual on the blended cost (`data/plant_cost_blended.csv`).

> **Network status (2026-06, Full access):** cercind.gov.in and coal.gov.in are
> reachable (CERC hosts the CIL price-notification archive used for layer a).
> grid-india.in / POSOCO eLibrary / meritindia.in returned **HTTP 503**, so the
> FY2022-23 metered per-station ECR (layer d) could not be harvested. Re-run
> `analysis/07_fetch_ecr.py` when those feeds are back: it re-fetches the CIL prices
> and CERC orders and writes `plant_ecr.csv` only when a real FY2022-23 feed responds.
