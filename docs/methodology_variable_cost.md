# Methodology: the modelled variable-cost column

## The question
*"Is it possible to populate the variable-cost column?"*

**Short answer: not to plant accuracy from this file alone — but a transparent,
category-level estimate is possible and is what `02_variable_cost.py` builds.**

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
| Fuel price (₹/Gcal) | No | **Assumed** by source (editable block in the script) |
| Pithead vs distant, linkage vs e-auction, washery, blend | No | **Not captured** — the main residual |
| Non-fuel variable (oil + VOM) | No | Flat ₹0.20/kWh assumption |

## Assumptions (representative 2022-23 INR; edit in `02_variable_cost.py`)
- Fuel cost per Gcal of heat: lignite ₹500, domestic ₹850, imported ₹1700.
- Non-fuel variable adder: ₹0.20/kWh.
- Imported inferred when: name contains "imp", **or** GCV > 4800 kcal/kg,
  **or** the plant is on the curated `KNOWN_IMPORTED_KEYWORDS` list
  (Mundra, Coastal Energen, Udupi/UPCL, ITPCL, Essar …).

These reproduce the qualitative reality: imported plants ≈ ₹4.6/kWh (idle,
~27% PLF), lignite ≈ ₹1.8/kWh, domestic ≈ ₹2.5/kWh.

## The honest limitation
A **flat per-category** price makes the modelled variable cost track PLF (r≈−0.37,
R²≈14%) *worse* than efficiency (R²≈31%). Reasons:
1. ~90% of units are lumped into one "domestic" price, so within that bucket the
   modelled cost is just a rescaling of SHR — it adds no new information.
2. The real merit-order dispersion lives **inside** the domestic fleet
   (pithead-distance, grade, e-auction share, washery, freight), which a flat
   price cannot reproduce.
3. The GCV signal alone is unreliable — Mundra's as-fired GCV (~4090) is *below*
   the import threshold, so without the curated overlay it is mis-labelled domestic.

**Conclusion:** the category model is directionally correct (imported ⇒ expensive
⇒ backed down) but cannot, by itself, beat efficiency or be treated as
plant-accurate.

## Refinement now in place: grade-aware domestic pricing
Each plant is tagged with its official **Ministry-of-Coal non-coking coal grade
(G1–G17)** from its GCV (real 300 kcal/kg slabs, `common.grade_from_gcv`), and
domestic coal is priced **by grade** rather than one flat number
(`DOMESTIC_GRADE_PRICE_MULTIPLIER` in `02_variable_cost.py`). Lower grades carry
a modestly higher ₹/Gcal (fixed per-tonne handling/freight over less heat),
mirroring CIL notified-price behaviour. The grade *slabs* are authoritative; the
*multipliers* remain representative until overridden by real ECR.

## How to make it accurate — the ECR override layer (`06_apply_ecr.py`)
Replace the assumed prices with **plant-level Energy Charge Rate (ECR)**, which
*is* published:
- **CERC / SERC tariff orders** (regulated central & state stations).
- **Merit Order Despatch / "energy charge rate"** sheets from RLDCs / Grid-India
  / the MERIT portal (meritindia.in).
- **CEA** fuel-cost and coal-source databases.

**Workflow:** copy `data/raw/plant_ecr_template.csv` → `data/raw/plant_ecr.csv`,
fill it (`match_name, ecr_rs_per_kwh, period, source`), and run
`python3 analysis/06_apply_ecr.py`. It fuzzy-matches station names, overrides the
modelled cost where real ECR exists (else falls back to the model), tracks a
`vc_source` flag and coverage, and re-runs the cost-vs-carbon counterfactual on
the blended cost. Output: `data/plant_cost_blended.csv`.

**Worked example (shipped seed):** the model priced **Talcher at ~₹2.7/kWh**, but
its **real CERC ECR is ₹1.48/kWh** — Talcher is *pithead*, which the GCV/source
model cannot infer. This single real row shows the override changing a station's
cost by ~45% in the right direction (and Talcher runs at 75–90% PLF). Pithead
distance, e-auction share and freight only enter with real ECR.

> **Network note:** cercind.gov.in / coal.gov.in / grid-india / meritindia.in
> return HTTP 403 in this remote environment, so the full table cannot be
> harvested in-session. Fetch locally (or allow-list those domains); the layer
> then consumes the CSV unchanged.
