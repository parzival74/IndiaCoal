"""
02 - EXTENSION #1: Variable cost (Rs/kWh) -- the variable that merit order
     *actually* dispatches on.

    variable_cost (Rs/kWh) = SHR (kcal/kWh) * fuel_price (Rs/Gcal) / 1e6
                             + non_fuel_variable (Rs/kWh)

SHR is real (per plant). The fuel price is where the work is:

  * DOMESTIC coal is now priced on REAL, vintage-correct data: the Coal India
    Limited FY2022-23 grade-wise PITHEAD notified price (Rs/tonne) from
    data/raw/cil_grade_prices_fy2022-23.csv (CIL notif. 194 dated 27-11-2020,
    the schedule in force across all of FY2022-23). On top of the ex-mine price
    we add the published statutory levies (royalty, GST, GST compensation cess)
    and a flagged transport term -- see the build-up below.
  * LIGNITE and IMPORTED coal keep MODELLED Rs/Gcal anchors: CIL's notified
    price does not cover them (lignite is captive mine-mouth; imported is
    seaborne), and no real per-station FY2022-23 ECR could be fetched for them.

WHAT IS REAL vs MODELLED HERE:
  REAL (published, FY2022-23):  CIL pithead Rs/tonne by grade; royalty 14%;
                                GST 5%; GST compensation cess Rs400/t; each
                                plant's SHR and GCV.
  MODELLED (flagged):           rail freight (per-plant distance is NOT in the
                                dataset -> a single fleet-representative value;
                                this compresses the real pithead-vs-distant
                                spread, which the CERC cross-check in
                                08_cerc_crosscheck.py exposes); lignite &
                                imported Rs/Gcal anchors; non-fuel adder.

The genuinely FY2022-23 per-station metered ECR feeds (Grid-India SCED, POSOCO,
state SLDC, MERIT) were unreachable this session, so they do not override here;
the CERC tariff-order ECRs that ARE reachable are 2018-19 basis and are used only
as a labelled cross-check (08), never as the FY2022-23 headline. See
docs/methodology_variable_cost.md and docs/data_sources.md.

Run:  python3 analysis/02_variable_cost.py
Writes: data/cse_subcritical_clean.csv (adds cost columns), outputs/02_variable_cost.txt
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from scipy import stats
from common import (load_clean, analysis_set, CLEAN_CSV, OUT_DIR, REPO,
                    load_cil_pithead_prices, base_domestic_rs_per_tonne,
                    CIL_PRICE_CSV, CIL_OTHER_CHARGES_RS_PER_TONNE)

# --------------------------------------------------------------------------
# DOMESTIC COAL -- the REAL CIL pithead price + statutory levies build-up now
# lives in common.py. Here we add only the freight.
# --------------------------------------------------------------------------
# MODELLED, FLAGGED: average pit-to-plant rail freight. Per-plant lead distance is
# not in the dataset, so 02 uses one fleet-representative value (it deliberately
# CANNOT reproduce the pithead(~Rs0) vs distant(~Rs1500/t) spread -- the CERC
# cross-check in 08 shows the real per-station dispersion this flattens; 11
# replaces this flat term with a per-plant freight calibrated on real ISGS ECRs).
RAIL_FREIGHT_RS_PER_TONNE = 900.0

# --------------------------------------------------------------------------
# LIGNITE / IMPORTED -- MODELLED Rs/Gcal anchors (CIL notified price n/a).
# Representative FY2022-23 levels; not real per-station ECR (flagged below).
# --------------------------------------------------------------------------
FUEL_PRICE_RS_PER_GCAL_ANCHOR = {
    "lignite":  500.0,    # captive mine-mouth (e.g. NLC): cheap per tonne, low GCV
    "imported": 1700.0,   # seaborne (ICI GAR-4200); ~elevated in 2022-23
}
# Non-fuel variable cost (secondary fuel oil + variable O&M), Rs/kWh, flat.
NON_FUEL_VARIABLE_RS_PER_KWH = 0.20
# Source-inference signals.
IMPORTED_GCV_THRESHOLD = 4800.0  # kcal/kg; domestic Indian coal is high-ash/low-GCV
# Curated overlay of well-known imported / imported-blend coastal stations. GCV
# alone is unreliable (Mundra's as-fired GCV ~4090 < threshold); overlay public
# knowledge keyed on plant/company name. Documented in methodology_variable_cost.md.
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


def domestic_landed_rs_per_gcal(grade: str, gcv: float, pithead: dict):
    """Real CIL pithead price + published levies + flagged flat freight -> Rs/Gcal."""
    base = base_domestic_rs_per_tonne(grade, pithead)  # pithead + levies (shared)
    if base is None or pd.isna(gcv) or gcv <= 0:
        return np.nan
    landed_rs_per_tonne = base + RAIL_FREIGHT_RS_PER_TONNE  # + flat freight (MODELLED)
    # Rs/tonne -> Rs/Gcal using the plant's actual GCV (Gcal/tonne = GCV/1000).
    return landed_rs_per_tonne * 1000.0 / gcv


def add_variable_cost(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    pithead = load_cil_pithead_prices()
    df["coal_source"] = df.apply(classify_source, axis=1)

    dom_gcal = df.apply(
        lambda r: domestic_landed_rs_per_gcal(r["coal_grade"], r["gcv_kcal_per_kg"], pithead),
        axis=1)
    anchor = df["coal_source"].map(FUEL_PRICE_RS_PER_GCAL_ANCHOR)
    df["fuel_price_rs_per_gcal"] = np.where(df["coal_source"] == "domestic", dom_gcal, anchor)
    df["fuel_price_basis"] = np.where(
        df["coal_source"] == "domestic", "CIL_pithead_FY2022-23+levies+freight", "modelled_anchor")
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

    using_csv = os.path.exists(CIL_PRICE_CSV)
    log("=" * 70)
    log("EXTENSION #1 - VARIABLE COST (Rs/kWh)")
    log("=" * 70)
    log("DOMESTIC coal: REAL CIL FY2022-23 pithead price (Rs/tonne, by grade) "
        + ("from data/raw/cil_grade_prices_fy2022-23.csv" if using_csv
           else "[inline verified fallback - CSV not found]"))
    log("  landed Rs/tonne = pithead*(1 + royalty 0.14 + GST 0.05) + cess Rs400 "
        f"+ sizing Rs{CIL_OTHER_CHARGES_RS_PER_TONNE:.0f} + freight Rs{RAIL_FREIGHT_RS_PER_TONNE:.0f}")
    log("  (royalty/GST/cess = published statutory rates; freight = MODELLED, "
        "flagged: per-plant lead distance is not in the dataset)")
    log("LIGNITE / IMPORTED: MODELLED Rs/Gcal anchors "
        + str(FUEL_PRICE_RS_PER_GCAL_ANCHOR) + " (CIL price n/a; not real ECR)")
    log(f"Non-fuel adder: Rs {NON_FUEL_VARIABLE_RS_PER_KWH}/kWh\n")

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
    log("Does variable cost track PLF better than efficiency? (PLF>=20)")
    log("-" * 70)
    log(f"  PLF ~ Efficiency        r={r_eff:+.3f}  R2={r_eff**2*100:.1f}%")
    log(f"  PLF ~ Variable cost     r={r_vc:+.3f}  R2={r_vc**2*100:.1f}%")
    log("  VC correlates NEGATIVELY (cheaper plants run more) -- the merit-order")
    log("  signal raw efficiency misses -- but with a flat freight term the within-")
    log("  domestic spread is compressed, so |r| stays modest (see 08 cross-check).")

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
