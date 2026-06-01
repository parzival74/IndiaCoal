"""
02 - EXTENSION #1: Modelled variable cost (Rs/kWh) -- the variable that
     merit order *actually* dispatches on.

CAN WE POPULATE IT FROM THIS FILE? Not directly. The file has SHR and GCV but
NOT the per-plant coal price, which is the dominant term. So we MODEL it:

    variable_cost (Rs/kWh) = SHR (kcal/kWh) * fuel_price (Rs/Gcal) / 1e6
                             + non_fuel_variable (Rs/kWh)

SHR is real (per plant). fuel_price is assigned by inferred coal SOURCE, using
representative 2022-23 benchmarks. The source is inferred from signals we DO
have: fuel type (Lignite), coal GCV, and "imp" in the plant name.

The price block below is the ONLY set of assumptions; edit it (or replace with
plant-level CERC Energy Charge Rate filings) to make the numbers contract-accurate.
This is a transparent estimate, not metered cost -- see docs/methodology_variable_cost.md.

Run:  python3 analysis/02_variable_cost.py
Writes: data/plant_variable_cost.csv, outputs/02_variable_cost.txt
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from scipy import stats
from common import load_clean, analysis_set, CLEAN_CSV, OUT_DIR

# --------------------------------------------------------------------------
# ASSUMPTIONS  (representative 2022-23 INR; edit these for your own scenario)
# --------------------------------------------------------------------------
# Fuel cost per Gcal of heat input (separates fuel PRICE from plant EFFICIENCY).
FUEL_PRICE_RS_PER_GCAL = {
    "lignite":  500.0,   # captive mine-mouth: cheap per tonne, low GCV
    "domestic": 850.0,   # CIL linkage coal, landed (washing + rail freight)
    "imported": 1700.0,  # seaborne thermal coal, ~2x domestic in 2022-23
}
# Non-fuel variable cost (secondary fuel oil + variable O&M), Rs/kWh, flat.
NON_FUEL_VARIABLE_RS_PER_KWH = 0.20
# Source-inference thresholds.
IMPORTED_GCV_THRESHOLD = 4800.0  # kcal/kg; domestic Indian coal is high-ash/low-GCV
# Curated overlay of well-known imported / imported-blend coastal stations.
# GCV alone is unreliable (e.g. Mundra's as-fired GCV ~4090 < threshold), so we
# overlay public knowledge keyed on plant/company name. THIS IS A STOP-GAP: the
# authoritative fix is to join CEA's per-unit coal-source field. Documented in
# docs/methodology_variable_cost.md.
KNOWN_IMPORTED_KEYWORDS = [
    "mundra",        # Adani Power, Gujarat - Indonesian imported coal
    "coastal",       # Coastal Energen (Mutiara), Tamil Nadu - imported
    "muthiara",      # = Coastal Energen Melamaruthur
    "upcl",          # Udupi Power Corp, Karnataka - imported
    "itpcl",         # IL&FS Tamil Nadu (Cuddalore) - imported
    "il&fs",         # ditto
    "essar",         # Essar (Salaya), Gujarat - imported
]
# --------------------------------------------------------------------------


def classify_source(row) -> str:
    if str(row["fuel"]).strip().lower() == "lignite":
        return "lignite"
    name = str(row["name"]).lower()
    company = str(row["company"]).lower()
    hay = name + " " + company
    if (("imp" in name)
            or any(k in hay for k in KNOWN_IMPORTED_KEYWORDS)
            or (pd.notna(row["gcv_kcal_per_kg"])
                and row["gcv_kcal_per_kg"] > IMPORTED_GCV_THRESHOLD)):
        return "imported"
    return "domestic"


def add_variable_cost(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["coal_source"] = df.apply(classify_source, axis=1)
    df["fuel_price_rs_per_gcal"] = df["coal_source"].map(FUEL_PRICE_RS_PER_GCAL)
    df["vc_fuel_rs_per_kwh"] = (
        df["shr_kcal_per_kwh"] * df["fuel_price_rs_per_gcal"] / 1e6)
    df["variable_cost_rs_per_kwh"] = (
        df["vc_fuel_rs_per_kwh"] + NON_FUEL_VARIABLE_RS_PER_KWH)
    return df


def main():
    lines = []
    log = lines.append
    df = add_variable_cost(load_clean())
    df.to_csv(CLEAN_CSV, index=False)  # persist the new columns back

    log("=" * 70)
    log("EXTENSION #1 - MODELLED VARIABLE COST (Rs/kWh)")
    log("=" * 70)
    log("Assumptions (Rs/Gcal of heat): " + str(FUEL_PRICE_RS_PER_GCAL))
    log(f"Non-fuel variable adder: Rs {NON_FUEL_VARIABLE_RS_PER_KWH}/kWh")
    log(f"Imported-coal GCV threshold: {IMPORTED_GCV_THRESHOLD} kcal/kg\n")

    log("Coal-source split (inferred):")
    log(df["coal_source"].value_counts().to_string())

    log("\nVariable cost & PLF by inferred source:")
    g = df.groupby("coal_source").agg(
        n=("variable_cost_rs_per_kwh", "size"),
        VC=("variable_cost_rs_per_kwh", "mean"),
        Eff=("efficiency_pct", "mean"),
        PLF=("plf_pct", "mean"),
        EF=("ef_t_per_mwh", "mean")).round(2)
    log(g.to_string())

    # The headline test: does VC explain PLF better than efficiency?
    sub = analysis_set(df)
    def pr(col):
        m = sub[col].notna() & sub["plf_pct"].notna()
        r, _ = stats.pearsonr(sub[col][m], sub["plf_pct"][m])
        return r
    r_eff = pr("efficiency_pct")
    r_vc = pr("variable_cost_rs_per_kwh")
    log("\n" + "-" * 70)
    log("Does modelled variable cost track PLF better than efficiency? (PLF>=20)")
    log("-" * 70)
    log(f"  PLF ~ Efficiency        r={r_eff:+.3f}  R2={r_eff**2*100:.1f}%")
    log(f"  PLF ~ Variable cost     r={r_vc:+.3f}  R2={r_vc**2*100:.1f}%")
    log("  (variable cost should correlate NEGATIVELY and more strongly --")
    log("   cheaper plants run more. This is the merit-order signal that raw")
    log("   efficiency misses.)")

    # The smoking guns
    log("\nIllustrative cases (efficiency vs cost pull opposite ways):")
    show = ["name", "company", "coal_source", "efficiency_pct",
            "variable_cost_rs_per_kwh", "plf_pct", "ef_t_per_mwh"]
    mundra = df[df["name"].str.contains("Mundra", case=False, na=False)]
    lignite = df[df["coal_source"] == "lignite"].nlargest(3, "plf_pct")
    log("  -- Efficient but EXPENSIVE (imported) -> idle:")
    log(mundra[show].head(2).to_string(index=False))
    log("  -- Inefficient but CHEAP (lignite) -> busy:")
    log(lignite[show].to_string(index=False))

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "02_variable_cost.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[wrote {out}; variable-cost columns persisted to {CLEAN_CSV}]")


if __name__ == "__main__":
    main()
