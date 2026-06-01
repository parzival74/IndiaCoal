"""
06 - Apply REAL plant-level Energy Charge Rate (ECR), overriding the modelled
     variable cost from 02 wherever published data is available.

This is the answer to "replace assumed prices with plant-level ECR". The model
in 02 is a fallback; this step lets authoritative per-station ₹/kWh from
  - CERC / SERC tariff orders (regulated central & state stations),
  - RLDC / Grid-India / MERIT merit-order-despatch ("energy charge rate") sheets,
  - CEA fuel-cost / coal-source databases,
drop straight in via data/raw/plant_ecr.csv and take precedence.

INPUT  data/raw/plant_ecr.csv  (a template is shipped; replace with real data)
    columns: match_name, ecr_rs_per_kwh, period, source
             match_name      -> station name (fuzzy-matched to the plant table)
             ecr_rs_per_kwh   -> published energy charge / variable cost, ₹/kWh
             period           -> e.g. "FY2022-23" (provenance)
             source           -> citation (CERC order no., MOD sheet, URL)

OUTPUT a blended variable_cost_final (real ECR where matched, else modelled),
       a per-row vc_source flag, a coverage report, and a re-run of the
       cost-vs-carbon counterfactual on the blended cost.

NETWORK NOTE: this environment blocks cercind.gov.in / coal.gov.in / grid-india /
meritindia.in (HTTP 403), so the table cannot be auto-harvested here. Run locally
(or with those domains allow-listed) to fetch them; this layer then consumes them.

Depends on: 02_variable_cost.py (modelled variable_cost_rs_per_kwh).
Run:  python3 analysis/06_apply_ecr.py
Writes: data/plant_cost_blended.csv, outputs/06_apply_ecr.txt
"""
from __future__ import annotations
import os
import re
import difflib
import numpy as np
import pandas as pd
from common import load_clean, REPO, OUT_DIR

ECR_CSV = os.path.join(REPO, "data", "raw", "plant_ecr.csv")
TEMPLATE_CSV = os.path.join(REPO, "data", "raw", "plant_ecr_template.csv")
OUT_CSV = os.path.join(REPO, "data", "plant_cost_blended.csv")
HOURS, MAX_PLF = 8760, 0.85
MATCH_CUTOFF = 0.82  # difflib ratio threshold for a confident station match


def _norm(s: str) -> str:
    """Normalise a station name for matching (drop punctuation, suffixes, case)."""
    s = str(s).lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    for junk in ["tps", "tpp", "stps", "tps", "ctps", "ext", "extn", "expansion",
                 "stage", "unit", "power", "thermal", "station", "ltd", "limited",
                 "new", "old", "ph", "phase"]:
        s = re.sub(rf"\b{junk}\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def match_ecr(plants: pd.DataFrame, ecr: pd.DataFrame):
    """Fuzzy-match ECR rows to plant stations; return matched map + diagnostics."""
    plants = plants.copy()
    plants["_key"] = plants["name"].map(_norm)
    keys = plants["_key"].unique().tolist()
    rows = []
    name_to_ecr = {}
    for _, r in ecr.iterrows():
        k = _norm(r["match_name"])
        hit = difflib.get_close_matches(k, keys, n=1, cutoff=MATCH_CUTOFF)
        matched = hit[0] if hit else None
        rows.append({"ecr_name": r["match_name"], "ecr_rs_per_kwh": r["ecr_rs_per_kwh"],
                     "matched_key": matched, "source": r.get("source", "")})
        if matched is not None:
            name_to_ecr[matched] = r["ecr_rs_per_kwh"]
    plants["ecr_rs_per_kwh"] = plants["_key"].map(name_to_ecr)
    return plants, pd.DataFrame(rows)


def redispatch(df, order_col, ascending, total_gwh):
    d = df.sort_values(order_col, ascending=ascending).copy()
    cap = d["capacity_mw"] * HOURS * MAX_PLF / 1000.0
    gen, rem = np.zeros(len(d)), total_gwh
    for i, c in enumerate(cap.values):
        if rem <= 0:
            break
        take = min(c, rem); gen[i] = take; rem -= take
    d["_g"] = gen
    cost = (d["_g"] * 1e6 * d["variable_cost_final"]).sum() / 1e7
    co2 = (d["_g"] * d["ef_t_per_mwh"] / 1000.0).sum()
    return cost, co2


def main():
    lines = []
    log = lines.append
    df = load_clean()
    if "variable_cost_rs_per_kwh" not in df.columns:
        raise SystemExit("Run analysis/02_variable_cost.py first.")

    log("=" * 70)
    log("06 - APPLY PLANT-LEVEL ECR (real data overrides the model)")
    log("=" * 70)

    path = ECR_CSV if os.path.exists(ECR_CSV) else TEMPLATE_CSV
    ecr = pd.read_csv(path, comment="#")
    using_real = os.path.exists(ECR_CSV)
    log(f"ECR source file: {os.path.relpath(path, REPO)} "
        f"({'REAL user data' if using_real else 'shipped TEMPLATE - replace with real ECR'})")
    log(f"ECR rows supplied: {len(ecr)}")

    df, diag = match_ecr(df, ecr)
    n_match = df["ecr_rs_per_kwh"].notna().sum()
    log(f"\nMatched {n_match}/{len(df)} units to a published ECR "
        f"({100*n_match/len(df):.1f}% coverage); the rest fall back to the model.")

    # Blend: real ECR where present, else modelled variable cost.
    df["variable_cost_final"] = df["ecr_rs_per_kwh"].fillna(df["variable_cost_rs_per_kwh"])
    df["vc_source"] = np.where(df["ecr_rs_per_kwh"].notna(), "published_ECR", "modelled")
    df.drop(columns=["_key"]).to_csv(OUT_CSV, index=False)

    log("\nMatch diagnostics (ECR row -> plant key):")
    log(diag.to_string(index=False))

    if n_match:
        log("\nWhere real ECR replaced the model:")
        shown = df[df["ecr_rs_per_kwh"].notna()][
            ["name", "coal_source", "coal_grade",
             "variable_cost_rs_per_kwh", "ecr_rs_per_kwh", "plf_pct"]]
        log(shown.to_string(index=False))

    # Re-run the cost-vs-carbon counterfactual on the blended cost.
    d = df.dropna(subset=["capacity_mw", "net_gen_gwh", "variable_cost_final",
                          "ef_t_per_mwh"]).copy()
    total = d["net_gen_gwh"].sum()
    base_cost = (d["net_gen_gwh"] * 1e6 * d["variable_cost_final"]).sum() / 1e7
    base_co2 = (d["net_gen_gwh"] * d["ef_t_per_mwh"] / 1000.0).sum()
    cm_cost, cm_co2 = redispatch(d, "variable_cost_final", True, total)
    cb_cost, cb_co2 = redispatch(d, "ef_t_per_mwh", True, total)
    log("\n" + "-" * 70)
    log("Cost-vs-carbon re-dispatch on the BLENDED cost (same total energy):")
    log("-" * 70)
    log(f"  Actual      : fuel cost Rs {base_cost:,.0f} cr | CO2 {base_co2:,.1f} MT")
    log(f"  Cost-merit  : fuel cost Rs {cm_cost:,.0f} cr | CO2 {cm_co2:,.1f} MT")
    log(f"  Carbon-merit: fuel cost Rs {cb_cost:,.0f} cr | CO2 {cb_co2:,.1f} MT")
    log(f"  Cost-vs-carbon gap: {cm_co2-cb_co2:+,.1f} MT CO2 for "
        f"Rs {cb_cost-cm_cost:+,.0f} cr.")

    if not using_real:
        log("\n>>> This ran on the TEMPLATE. Drop real CERC/MOD/CEA ECR into")
        log(">>> data/raw/plant_ecr.csv and re-run to raise coverage above the")
        log(">>> few seeded rows. See docs/data_sources.md for where to fetch it.")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "06_apply_ecr.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[wrote {out} and {os.path.relpath(OUT_CSV, REPO)}]")


if __name__ == "__main__":
    main()
