"""
01 - Reproduce the headline Efficiency<->PLF correlations and decompose PLF
     with a multivariate OLS over every usable plant-technical variable.

Run:  python3 analysis/01_correlations.py
Writes: outputs/01_correlations.txt
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from scipy import stats
from common import load_clean, analysis_set, OUT_DIR


def pearson(a: pd.Series, b: pd.Series):
    m = a.notna() & b.notna()
    r, p = stats.pearsonr(a[m], b[m])
    return r, r * r, int(m.sum())


def ols(y: np.ndarray, X: np.ndarray):
    """Plain OLS with intercept; returns betas, R2, adjusted R2."""
    Xd = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(Xd, y, rcond=None)
    yhat = Xd @ beta
    ss_res = float(((y - yhat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot
    n, k = Xd.shape
    adj = 1 - (1 - r2) * (n - 1) / (n - k)
    return beta, r2, adj


def z(s: pd.Series) -> np.ndarray:
    s = pd.to_numeric(s, errors="coerce")
    return ((s - s.mean()) / s.std()).values


def main():
    lines = []
    log = lines.append
    df = load_clean()

    # ---- Headline correlations -------------------------------------------
    log("=" * 70)
    log("HEADLINE: Efficiency vs PLF")
    log("=" * 70)
    r, r2, n = pearson(df["efficiency_pct"], df["plf_pct"])
    log(f"  ALL units      r={r:.3f}  R2={r2*100:.1f}%  n={n}")
    sub = analysis_set(df)
    r, r2, n = pearson(sub["efficiency_pct"], sub["plf_pct"])
    log(f"  PLF>=20 units  r={r:.3f}  R2={r2*100:.1f}%  n={n}")
    log(f"  (units dropped with PLF<20: {(df['plf_pct']<20).sum()})")

    # ---- Univariate r of PLF vs each driver (PLF>=20) --------------------
    log("\n" + "=" * 70)
    log("UNIVARIATE: PLF vs each driver (PLF>=20 set)")
    log("=" * 70)
    drivers = {
        "efficiency_pct": "Efficiency (%)",
        "shr_kcal_per_kwh": "Station heat rate",
        "aux_pct": "Auxiliary consumption (%)",
        "ef_t_per_mwh": "Emission factor (t/MWh)",
        "capacity_mw": "Capacity (MW)",
        "gcv_kcal_per_kg": "Coal GCV",
        "age_yr": "Age (yr)",
    }
    for col, label in drivers.items():
        r, r2, n = pearson(sub[col], sub["plf_pct"])
        log(f"  PLF ~ {label:28s} r={r:+.3f}  R2={r2*100:4.1f}%")

    # ---- Group means ------------------------------------------------------
    log("\n" + "=" * 70)
    log("PLF & Efficiency by sector (PLF>=20)")
    log("=" * 70)
    g = sub.groupby("sector").agg(
        n=("plf_pct", "size"), PLF=("plf_pct", "mean"),
        Eff=("efficiency_pct", "mean"), Age=("age_yr", "mean"),
        Cap=("capacity_mw", "mean")).round(1)
    log(g.to_string())

    for col, edges, labs, title in [
        ("capacity_mw", [0, 150, 250, 400, 1000], ["<150", "150-250", "250-400", "400+"], "capacity band (MW)"),
        ("age_yr", [0, 10, 20, 30, 40, 100], ["<10", "10-20", "20-30", "30-40", "40+"], "age band (yr)"),
    ]:
        sub["_band"] = pd.cut(sub[col], edges, labels=labs)
        g = sub.groupby("_band", observed=True).agg(
            n=("plf_pct", "size"), PLF=("plf_pct", "mean"),
            Eff=("efficiency_pct", "mean")).round(1)
        log(f"\nPLF by {title}:")
        log(g.to_string())

    # ---- Multivariate OLS -------------------------------------------------
    log("\n" + "=" * 70)
    log("MULTIVARIATE OLS: how much of PLF can plant-technical vars explain?")
    log("(standardised continuous predictors; sector base = State)")
    log("=" * 70)
    y = sub["plf_pct"].values
    cont = {k: z(sub[k]) for k in ["efficiency_pct", "age_yr", "capacity_mw", "gcv_kcal_per_kg", "aux_pct"]}
    dums = pd.get_dummies(sub["sector"])
    d_centre = dums.get("Centre", pd.Series(0, index=sub.index)).astype(float).values
    d_priv = dums.get("Private", pd.Series(0, index=sub.index)).astype(float).values

    models = [
        ("Efficiency only", ["efficiency_pct"]),
        ("+ Age + Capacity + GCV", ["efficiency_pct", "age_yr", "capacity_mw", "gcv_kcal_per_kg"]),
        ("+ Sector", ["efficiency_pct", "age_yr", "capacity_mw", "gcv_kcal_per_kg", "SEC"]),
        ("+ Auxiliary consumption (all)", ["efficiency_pct", "age_yr", "capacity_mw", "gcv_kcal_per_kg", "aux_pct", "SEC"]),
    ]
    for name, cols in models:
        parts, labels = [], []
        for c in cols:
            if c == "SEC":
                parts += [d_centre, d_priv]
                labels += ["Centre(vs State)", "Private(vs State)"]
            else:
                parts.append(cont[c])
                labels.append(c)
        X = np.column_stack(parts)
        beta, r2, adj = ols(y, X)
        log(f"\n  {name}:  R2={r2*100:.1f}%  adjR2={adj*100:.1f}%")
        log(f"    intercept (mean PLF) = {beta[0]:.1f}")
        for lab, b in zip(labels, beta[1:]):
            log(f"    {lab:20s} {b:+.2f}")

    log("\nTakeaway: every measurable plant variable combined still leaves ~56%")
    log("of PLF variation unexplained -> the dispatch drivers (fuel cost,")
    log("PPA/must-run, RE backing-down, grid location) are NOT in this dataset.")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "01_correlations.txt")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n[wrote {out}]")


if __name__ == "__main__":
    main()
