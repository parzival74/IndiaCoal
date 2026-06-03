"""
03 - EXTENSION #2: Grid-region classification, to frame the "proximity to
     load centres" hypothesis (H2).

The file has NO state/location/grid-node column. We infer the grid region from
the COMPANY field, which is reliable for state utilities (SEB acronyms map to a
state -> region) but NOT for NTPC / central / large IPPs, whose units span
regions. Those are tagged "Unallocated" and excluded from the regional means.

IMPORTANT: grid region is only a COARSE proxy for electrical proximity to load.
H2 (nearness to load pockets) really needs nodal / load-pocket / RLDC-bus data,
which is not in this dataset. This step frames the question; it cannot settle it.

Run:  python3 analysis/03_regions.py
Writes: outputs/03_regions.txt  (and a region column persisted to the clean CSV)
"""
from __future__ import annotations
import os
import pandas as pd
from common import load_clean, analysis_set, CLEAN_CSV, OUT_DIR

# Company keyword -> grid region (NR/WR/SR/ER). State utilities only; high conf.
COMPANY_REGION = {
    # Northern Region
    "uprvunl": "NR", "rrvunl": "NR", "rvunl": "NR", "pseb": "NR",
    "hpgcl": "NR", "rosa": "NR", "lanco anapara": "NR", "bajaj": "NR",
    # Western Region
    "mahagenco": "WR", "gsecl": "WR", "mppgcl": "WR", "mpgpcl": "WR",
    "cseb": "WR", "cspgcl": "WR", "gipcl": "WR", "gmdcl": "WR",
    "torr": "WR", "sai wardha": "WR", "raj west": "WR",
    # Southern Region
    "tneb": "SR", "tangedco": "SR", "apgenco": "SR", "kpcl": "SR",
    "tsgenco": "SR", "nlc": "SR", "ntpl": "SR", "singareni": "SR",
    "gvk": "SR", "upcl": "SR",
    # Eastern Region
    "wbpdc": "ER", "dvc": "ER", "bseb": "ER", "cesc": "ER", "tvnl": "ER",
    "bpscl": "ER", "opgc": "ER", "haldia": "ER", "dpl": "ER",
}
REGION_NAME = {"NR": "Northern", "WR": "Western", "SR": "Southern", "ER": "Eastern"}


def region_of(company: str) -> str:
    c = str(company).lower()
    for kw, reg in COMPANY_REGION.items():
        if kw in c:
            return reg
    return "Unallocated"


def main():
    lines = []
    log = lines.append
    df = load_clean()
    df["grid_region"] = df["company"].map(region_of)
    df.to_csv(CLEAN_CSV, index=False)

    n_class = (df["grid_region"] != "Unallocated").sum()
    log("=" * 70)
    log("EXTENSION #2 - GRID REGION (coarse proxy for H2 'proximity to load')")
    log("=" * 70)
    log(f"Classified {n_class}/{len(df)} units "
        f"({100*n_class/len(df):.0f}%); rest are central/IPP -> Unallocated.\n")
    log(df["grid_region"].value_counts().to_string())

    sub = analysis_set(df)
    classed = sub[sub["grid_region"] != "Unallocated"].copy()
    classed["region_name"] = classed["grid_region"].map(REGION_NAME)
    log("\nPLF / efficiency by region (state-utility subset, PLF>=20):")
    g = classed.groupby("region_name").agg(
        n=("plf_pct", "size"), PLF=("plf_pct", "mean"),
        Eff=("efficiency_pct", "mean"), Age=("age_yr", "mean"),
        Cap=("capacity_mw", "mean")).round(1)
    log(g.to_string())

    log("\nCAVEAT: region != load-pocket. Western India's lower/higher PLF here")
    log("cannot confirm the 'nearer to load / faster solar-ramp response'")
    log("hypothesis -- that needs nodal dispatch (SCED) data (see extension #3).")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "03_regions.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[wrote {out}; grid_region persisted to {CLEAN_CSV}]")


if __name__ == "__main__":
    main()
