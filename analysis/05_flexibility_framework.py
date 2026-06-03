"""
05 - EXTENSION #3: Flexibility / fast-ramp framework (Hypothesis H1).

WHY THIS IS A FRAMEWORK, NOT A RESULT
-------------------------------------
H1 says small/old Western plants earn dispatch by ramping fast for the evening
solar-drop + demand-rise. Annual PLF CANNOT see this: PLF is a yearly ENERGY
average, while flexibility is a sub-daily behaviour (ramp rate, start/stop
cycling, two-shifting, response to the net-load ramp). Our 01_correlations.py
already shows age has ~0 correlation with annual PLF -- but that neither
confirms nor refutes H1, because the relevant signal lives in block-level data.

This module:
  (a) defines the metrics that DO test H1,
  (b) specifies the block-level input schema and where to get it (docs/data_sources.md),
  (c) computes those metrics from any conforming dataframe, and
  (d) runs on a small SYNTHETIC sample so the pipeline is testable offline.

The remote environment blocks Grid-India/CEA, so live SCED data is not fetched
here. Drop a real block-level CSV at data/raw/sced_blocks.csv (schema below) and
re-run to get real flexibility metrics.

Run:  python3 analysis/05_flexibility_framework.py
Writes: outputs/05_flexibility_framework.txt
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from common import OUT_DIR, REPO

# Expected block-level schema (15-min or hourly):
#   unit_id        str    matches a unit in the plant table
#   timestamp      datetime
#   mw             float  scheduled/actual generation in that block
#   capacity_mw    float  nameplate (for normalised ramp)
SCED_PATH = os.path.join(REPO, "data", "raw", "sced_blocks.csv")


def flexibility_metrics(blocks: pd.DataFrame) -> pd.DataFrame:
    """Per-unit flexibility metrics from block-level generation."""
    blocks = blocks.sort_values(["unit_id", "timestamp"]).copy()
    blocks["mw_prev"] = blocks.groupby("unit_id")["mw"].shift(1)
    blocks["ramp_mw"] = (blocks["mw"] - blocks["mw_prev"]).abs()
    blocks["ramp_pct_cap"] = 100 * blocks["ramp_mw"] / blocks["capacity_mw"]
    # A "start" = transition from ~0 to generating (two-shifting signal)
    on = blocks["mw"] > 0.05 * blocks["capacity_mw"]
    on_prev = blocks.groupby("unit_id")["mw"].shift(1) > 0.05 * blocks["capacity_mw"]
    blocks["is_start"] = (on & ~on_prev.fillna(False)).astype(int)

    g = blocks.groupby("unit_id").agg(
        blocks=("mw", "size"),
        mean_mw=("mw", "mean"),
        max_ramp_pct_cap=("ramp_pct_cap", "max"),
        p95_ramp_pct_cap=("ramp_pct_cap", lambda s: np.nanpercentile(s, 95)),
        starts=("is_start", "sum"),
        min_mw=("mw", "min"),
    ).round(2)
    # Technical minimum reached (low = more flexible)
    g["min_load_pct_cap"] = (100 * g["min_mw"] /
                             blocks.groupby("unit_id")["capacity_mw"].first()).round(1)
    return g.drop(columns="min_mw")


def synthetic_blocks() -> pd.DataFrame:
    """Two illustrative units over 3 days of 15-min blocks: one flexible
    (two-shifting, deep evening ramp) and one baseload (flat)."""
    rng = pd.date_range("2024-04-01", periods=96 * 3, freq="15min")
    hour = rng.hour + rng.minute / 60.0
    # Flexible peaker: off midday (solar), ramps hard into evening peak
    flex = 300 * np.clip((np.sin((hour - 6) / 24 * 2 * np.pi) * -1 + 0.3), 0, 1)
    flex = np.where((hour > 9) & (hour < 16), 0.0, flex)  # backed down midday
    # Baseload: ~flat near 85%
    base = np.full_like(hour, 0.85 * 250)
    out = pd.concat([
        pd.DataFrame({"unit_id": "FLEX_WR_old_150MW", "timestamp": rng,
                      "mw": flex, "capacity_mw": 300}),
        pd.DataFrame({"unit_id": "BASE_central_250MW", "timestamp": rng,
                      "mw": base, "capacity_mw": 250}),
    ], ignore_index=True)
    return out


def main():
    lines = []
    log = lines.append
    log("=" * 70)
    log("EXTENSION #3 - FLEXIBILITY FRAMEWORK (tests H1; needs block-level data)")
    log("=" * 70)

    if os.path.exists(SCED_PATH):
        blocks = pd.read_csv(SCED_PATH, parse_dates=["timestamp"])
        log(f"Loaded REAL block data: {SCED_PATH} ({len(blocks):,} rows)")
        synthetic = False
    else:
        blocks = synthetic_blocks()
        synthetic = True
        log("No real SCED file found at data/raw/sced_blocks.csv.")
        log("Running on SYNTHETIC demo data so the metrics are illustrated.")
        log("To test H1 for real, supply that file (see docs/data_sources.md).")

    log("\nPer-unit flexibility metrics"
        + (" [SYNTHETIC DEMO]" if synthetic else "") + ":")
    log(flexibility_metrics(blocks).to_string())

    log("\nHow to test H1 once real data is in place:")
    log("  1. Join these metrics to the plant table on unit_id.")
    log("  2. Regress ramp/starts/min-load on age, capacity, region, sector.")
    log("  3. H1 is supported only if SMALL/OLD/WESTERN units show HIGHER ramp")
    log("     rates and MORE starts (two-shifting) -- not higher annual PLF.")
    log("  4. Cross-check ramp timing against the evening net-load ramp")
    log("     (demand minus solar) from the same region.")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "05_flexibility_framework.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
