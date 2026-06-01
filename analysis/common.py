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
from scipy import stats

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


# ---------------------------------------------------------------------------
# Pithead proxy flag + a small correlation helper (shared by 09 and 10).
# There is no distance-to-mine field, so 'pithead' is a transparent CURATED
# PROXY: lignite (mine-mouth by construction) + a documented coal-belt list,
# each entry annotated with its coalfield basis. Matched by EXACT name. See the
# header of analysis/09_pithead_test.py for the full rationale and validation.
# ---------------------------------------------------------------------------
CORE_PITHEAD_COAL = {
    # --- Singrauli / Northern Coalfields (NCL) belt ---
    "Singrauli Stps":     "NTPC; Singrauli coalfield (NCL), mine-mouth",
    "Rihand":             "NTPC; Singrauli/Rihand (NCL Amlohri/Nigahi), mine-mouth",
    "Vindh_Chal Stps":    "NTPC Vindhyachal; Singrauli (NCL Nigahi/Jayant), mine-mouth",
    # --- Korba / South Eastern Coalfields (SECL) belt ---
    "Korba Stps":         "NTPC; Korba coalfield (SECL Kusmunda/Gevra), mine-mouth",
    "Sipat Stps":         "NTPC; Korba belt (SECL Dipka/Gevra), near-pithead",
    "Korba-West":         "CSPGCL; Korba coalfield, mine-mouth",
    "Korba-West Ext":     "CSPGCL; Korba coalfield, mine-mouth",
    "Korba-V(Dspm Tps)":  "CSPGCL/DSPM; Korba coalfield, mine-mouth",
    # --- Talcher / Mahanadi Coalfields (MCL) ---
    "Talcher Stps":       "NTPC; Talcher coalfield (MCL), mine-mouth",
    # --- Godavari valley / Singareni (SCCL) ---
    "R_Gundem Stps":      "NTPC Ramagundam; Singareni Godavari coalfield, mine-mouth",
    "R_Gundem - B":       "NTPC Ramagundam unit; Singareni Godavari coalfield, mine-mouth",
    "Singareni TPP":      "Singareni Collieries captive; Godavari coalfield, mine-mouth",
}
# Coal-belt but with non-trivial haul / weaker documentation; kept OUT of the
# primary flag and used only for sensitivity.
BORDERLINE_PITHEAD_COAL = {
    "Kahalgaon":                 "NTPC; Rajmahal coalfield (ECL) supply, longer haul",
    "Sanjay Gandhi":             "MPPGCL Birsinghpur; SECL Johilla coal-belt",
    "Mahan TPP":                 "private; Singrauli/Mahan coal-block area",
    "Raigarh TPP(OP Jindal Tps)":"JPL Raigarh; Gare-Pelma captive coal",
    "Chandrapur_Coal":           "MAHAGENCO Chandrapur; WCL Chandrapur coalfield",
    "Chandrapura":               "DVC Chandrapura; ECL/Bokaro coal-belt",
}


def flag_pithead(df: pd.DataFrame) -> pd.DataFrame:
    """Tag each row with a curated pithead PROXY: lignite + core coal list."""
    df = df.copy()
    df["is_lignite"] = df["fuel"].str.contains("Lignite", case=False, na=False)
    df["is_core_coal"] = df["name"].isin(CORE_PITHEAD_COAL)
    df["is_borderline"] = df["name"].isin(BORDERLINE_PITHEAD_COAL)
    # PRIMARY flag: lignite (structural mine-mouth) + undisputed coal pithead.
    df["pithead"] = df["is_lignite"] | df["is_core_coal"]
    return df


def corr(x: pd.Series, y: pd.Series):
    """Pearson r, R²=r², n on the pairwise-complete sample (None if n<3)."""
    m = x.notna() & y.notna()
    n = int(m.sum())
    if n < 3:
        return None, None, n
    r, _ = stats.pearsonr(x[m], y[m])
    return float(r), float(r * r), n


# ---------------------------------------------------------------------------
# Domestic-coal landed-price build-up (used by 02_variable_cost). REAL inputs:
# CIL FY2022-23 grade-wise PITHEAD price + published statutory levies. The ONLY
# modelled term is rail freight -- 02 uses a single flat value.
# ---------------------------------------------------------------------------
CIL_PRICE_CSV = os.path.join(REPO, "data", "raw", "cil_grade_prices_fy2022-23.csv")
# Inline fallback = verified Table-I "Power Utilities" pithead prices (Rs/tonne).
CIL_PITHEAD_ROM_FALLBACK = {
    "G2": 3298, "G3": 3154, "G4": 3010, "G5": 2747, "G6": 2327, "G7": 1936,
    "G8": 1475, "G9": 1150, "G10": 1034, "G11": 965, "G12": 896, "G13": 827,
    "G14": 758, "G15": 600, "G16": 574, "G17": 457,
}
ROYALTY_RATE = 0.14                      # ad-valorem royalty on the pithead price
GST_RATE = 0.05                          # GST on coal
GST_COMP_CESS_RS_PER_TONNE = 400.0       # fixed GST compensation cess
CIL_OTHER_CHARGES_RS_PER_TONNE = 150.0   # CIL-notified sizing/surface-transport


def load_cil_pithead_prices() -> dict:
    """Real CIL FY2022-23 grade-wise pithead price (Rs/tonne, Power-Utilities)."""
    if os.path.exists(CIL_PRICE_CSV):
        t = pd.read_csv(CIL_PRICE_CSV, comment="#")
        t = t.dropna(subset=["pithead_rom_rs_per_tonne_power"])
        return dict(zip(t["grade"], t["pithead_rom_rs_per_tonne_power"].astype(float)))
    return {k: float(v) for k, v in CIL_PITHEAD_ROM_FALLBACK.items()}


def base_domestic_rs_per_tonne(grade: str, pithead: dict):
    """Pithead price + statutory levies, EXCLUDING freight (Rs/tonne). None if no price."""
    p = pithead.get(grade)
    if p is None and str(grade).startswith("ungraded"):
        p = pithead.get("G17")   # sub-G17 coal (GCV<2200): floor at lowest notified grade
    if p is None:
        return None
    return (p * (1.0 + ROYALTY_RATE + GST_RATE)
            + GST_COMP_CESS_RS_PER_TONNE
            + CIL_OTHER_CHARGES_RS_PER_TONNE)


if __name__ == "__main__":
    d = clean_from_raw()
    os.makedirs(os.path.dirname(CLEAN_CSV), exist_ok=True)
    d.to_csv(CLEAN_CSV, index=False)
    print(f"Wrote {CLEAN_CSV}: {d.shape[0]} units x {d.shape[1]} cols")
    print("Columns:", list(d.columns))
