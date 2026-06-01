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

## How to make it accurate
Replace the assumed prices with **plant-level Energy Charge Rate (ECR)**, which
*is* published:
- **CERC / SERC tariff orders** (regulated central & state stations).
- **Merit Order Despatch / "energy charge rate"** sheets from RLDCs / Grid-India.
- **CEA** fuel-cost and coal-source databases.

Join those on unit/station and the variable-cost column becomes contract-accurate;
the `02_variable_cost.py` structure is built to accept that drop-in replacement.
