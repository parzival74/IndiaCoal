"""
04 - EXTENSION #4: Re-dispatch counterfactual.

Holds total fleet generation FIXED and re-stacks it under three merit orders,
to quantify the central finding: cost-optimal dispatch and carbon-optimal
dispatch pull in OPPOSITE directions for India's subcritical fleet.

  1. Actual          - generation as observed (the as-run baseline)
  2. Cost-merit      - cheapest modelled variable cost first
  3. Carbon-merit    - lowest emission factor (cleanest) first

For each unit, annual capability is capped at MAX_PLF of nameplate. Each plant's
variable cost and emission factor are held fixed (first-order: re-dispatch would
in reality shift part-load heat rates). Transmission limits, must-run status and
ramping are ignored -- this is a stylised stack model to size the trade-off, not
a production dispatch simulation.

Depends on: analysis/02_variable_cost.py (variable_cost column). Run that first.

Run:  python3 analysis/04_redispatch.py
Writes: outputs/04_redispatch.txt
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from common import load_clean, OUT_DIR

MAX_PLF = 0.85          # annual ceiling per unit when re-dispatched
HOURS = 8760


def dispatch(df: pd.DataFrame, order_col: str, ascending: bool, total_gwh: float):
    """Fill units in merit order up to capability until total_gwh is served."""
    d = df.sort_values(order_col, ascending=ascending).copy()
    cap_gwh = d["capacity_mw"] * HOURS * MAX_PLF / 1000.0
    gen = np.zeros(len(d))
    remaining = total_gwh
    for i, c in enumerate(cap_gwh.values):
        if remaining <= 0:
            break
        take = min(c, remaining)
        gen[i] = take
        remaining -= take
    d["_gen_gwh"] = gen
    cost_cr = (d["_gen_gwh"] * 1e6 * d["variable_cost_rs_per_kwh"]).sum() / 1e7
    co2_mt = (d["_gen_gwh"] * d["ef_t_per_mwh"] / 1000.0).sum()
    served = d["_gen_gwh"].sum()
    return cost_cr, co2_mt, served


def main():
    lines = []
    log = lines.append
    df = load_clean()
    if "variable_cost_rs_per_kwh" not in df.columns:
        raise SystemExit("Run analysis/02_variable_cost.py first (needs variable cost).")

    df = df.dropna(subset=["capacity_mw", "net_gen_gwh", "variable_cost_rs_per_kwh",
                           "ef_t_per_mwh"]).copy()
    total_gwh = df["net_gen_gwh"].sum()

    # Baseline = as-run
    base_cost = (df["net_gen_gwh"] * 1e6 * df["variable_cost_rs_per_kwh"]).sum() / 1e7
    base_co2 = (df["net_gen_gwh"] * df["ef_t_per_mwh"] / 1000.0).sum()

    log("=" * 70)
    log("EXTENSION #4 - RE-DISPATCH COUNTERFACTUAL (same total energy)")
    log("=" * 70)
    log(f"Fleet: {len(df)} units | total net generation held at {total_gwh:,.0f} GWh")
    log(f"Per-unit annual ceiling: {MAX_PLF:.0%} PLF | VC & EF held fixed\n")

    cm_cost, cm_co2, cm_served = dispatch(df, "variable_cost_rs_per_kwh", True, total_gwh)
    carb_cost, carb_co2, carb_served = dispatch(df, "ef_t_per_mwh", True, total_gwh)

    hdr = f"{'Scenario':<22}{'Fuel cost (Rs cr)':>20}{'CO2 (MT)':>14}{'Served (GWh)':>16}"
    log(hdr)
    log("-" * len(hdr))
    log(f"{'1. Actual (as-run)':<22}{base_cost:>20,.0f}{base_co2:>14,.1f}{total_gwh:>16,.0f}")
    log(f"{'2. Cost-merit':<22}{cm_cost:>20,.0f}{cm_co2:>14,.1f}{cm_served:>16,.0f}")
    log(f"{'3. Carbon-merit':<22}{carb_cost:>20,.0f}{carb_co2:>14,.1f}{carb_served:>16,.0f}")

    log("\nDeltas vs actual:")
    log(f"  Cost-merit   : fuel cost {cm_cost-base_cost:+,.0f} cr "
        f"({100*(cm_cost-base_cost)/base_cost:+.1f}%),  "
        f"CO2 {cm_co2-base_co2:+,.1f} MT ({100*(cm_co2-base_co2)/base_co2:+.1f}%)")
    log(f"  Carbon-merit : fuel cost {carb_cost-base_cost:+,.0f} cr "
        f"({100*(carb_cost-base_cost)/base_cost:+.1f}%),  "
        f"CO2 {carb_co2-base_co2:+,.1f} MT ({100*(carb_co2-base_co2)/base_co2:+.1f}%)")

    log("\nThe trade-off, isolated (cost-merit minus carbon-merit):")
    log(f"  Chasing least COST instead of least CARBON costs "
        f"{cm_co2-carb_co2:+,.1f} MT of extra CO2 "
        f"while saving {carb_cost-cm_cost:+,.0f} cr.")
    log("\nINTERPRETATION: minimum-cost and minimum-carbon dispatch are NOT the")
    log("same objective for this fleet. The cheapest units (pithead lignite/")
    log("domestic) are among the dirtiest; the cleanest (imported) are dearest.")
    log("So 'follow strict merit order' saves money but does not minimise CO2 --")
    log("the two goals require a carbon price to reconcile. (Magnitudes scale")
    log("with the fuel-price assumptions in 02_variable_cost.py.)")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "04_redispatch.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
