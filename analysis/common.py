"""
Shared utilities for the IndiaCoal subcritical-fleet analysis.

Source data: CSE analysis of CEA's CO2 database (2022-23, version 19),
"Table 1: Performance of Subcritical units operating in India".

NOTE ON VINTAGE & SCOPE
-----------------------
This table covers SUBCRITICAL units only. Supercritical and
ultra-supercritical (USC) plants -- India's most efficient -- are NOT in
this dataset. Any efficiency comparison with China's USC fleet is therefore
apples-to-oranges (see REPORT.md, section 4). The underlying CEA vintage is
2022-23, not 2024.
"""
from __future__ import annotations
import os
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_XLSX = os.path.join(REPO, "data", "raw",
                        "CSE_subcritical_coal_plants_CEA_2022-23.xlsx")
CLEAN_CSV = os.path.join(REPO, "data", "cse_subcritical_clean.csv")
OUT_DIR = os.path.join(REPO, "outputs")

# Official Ministry of Coal / Coal Controller non-coking coal GCV grade slabs
# (GCV kcal/kg, 300 kcal/kg bands). Source: coal.gov.in/major-statistics/coal-grades.
# (lower_bound_exclusive, grade) ordered high -> low.
COAL_GRADE_SLABS = [
    (7000, "G1"), (6700, "G2"), (6400, "G3"), (6100, "G4"), (5800, "G5"),
    (5500, "G6"), (5200, "G7"), (4900, "G8"), (4600, "G9"), (4300, "G10"),
    (4000, "G11"), (3700, "G12"), (3400, "G13"), (3100, "G14"), (2800, "G15"),
    (2500, "G16"), (2200, "G17"),
]


def grade_from_gcv(gcv) -> str:
    """Map a GCV (kcal/kg) to its official non-coking coal grade (G1-G17)."""
    if pd.isna(gcv):
        return "NA"
    for lower, grade in COAL_GRADE_SLABS:
        if gcv > lower:
            return grade
    return "ungraded(<2200)"


def load_clean() -> pd.DataFrame:
    """Load the cleaned plant-level CSV, building it from the raw xlsx if needed."""
    if not os.path.exists(CLEAN_CSV):
        clean_from_raw().to_csv(CLEAN_CSV, index=False)
    return pd.read_csv(CLEAN_CSV)


def clean_from_raw() -> pd.DataFrame:
    """Read the 'Working sheet', drop spacer columns, coerce numerics, rename."""
    df = pd.read_excel(RAW_XLSX, sheet_name="Working sheet")
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    df = df.rename(columns={
        "Sr. No.": "sr_no",
        "Name": "name",
        "Unit no.": "unit_no",
        "Company": "company",
        "Sector": "sector",
        "Age": "age_yr",
        "Average GCV": "gcv_kcal_per_kg",
        "Average GCV Range": "gcv_range",
        "Fuel": "fuel",
        "Capacity": "capacity_mw",
        "Emission factor (ton/MWh)": "ef_t_per_mwh",
        "PLF (per cent)": "plf_pct",
        "SHR (kcal/kWh)": "shr_kcal_per_kwh",
        "Efficiency (per cent)": "efficiency_pct",
        "Auxiliary Consumption (per cent)": "aux_pct",
        "Net generation (GWh)": "net_gen_gwh",
        "CO2 emissions (MT)": "co2_mt",
    })
    # PLF column carries two stray label rows ("Maximum/Minimum efficiency")
    for c in ["plf_pct", "efficiency_pct", "shr_kcal_per_kwh", "gcv_kcal_per_kg",
              "capacity_mw", "ef_t_per_mwh", "aux_pct", "net_gen_gwh", "co2_mt",
              "age_yr", "unit_no", "sr_no"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["plf_pct", "efficiency_pct"]).reset_index(drop=True)
    # Real, citable enrichment: official non-coking coal grade from GCV.
    df["coal_grade"] = df["gcv_kcal_per_kg"].apply(grade_from_gcv)
    return df


def analysis_set(df: pd.DataFrame, min_plf: float = 20.0) -> pd.DataFrame:
    """The PLF>=20 working set used for the headline correlations."""
    return df[df["plf_pct"] >= min_plf].copy()


if __name__ == "__main__":
    d = clean_from_raw()
    os.makedirs(os.path.dirname(CLEAN_CSV), exist_ok=True)
    d.to_csv(CLEAN_CSV, index=False)
    print(f"Wrote {CLEAN_CSV}: {d.shape[0]} units x {d.shape[1]} cols")
    print("Columns:", list(d.columns))
