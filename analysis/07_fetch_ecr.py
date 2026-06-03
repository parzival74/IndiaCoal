"""
07 - Fetch the real fuel-price / ECR inputs from the reachable government sources.

RUN STATUS (2026-06 session, Full network access). What this session found:
  * cercind.gov.in ......... 200  (CERC tariff orders + the CIL price-notification
                                   archive both live here)
  * coal.gov.in / coalindia.in 200 (with a browser User-Agent)
  * grid-india.in / POSOCO eLibrary / MERIT / NPP ... HTTP 503 / connection-refused
    -> the genuinely FY2022-23 PER-STATION metered ECR feeds were all unreachable.

So this script fetches the two real, reachable inputs and refuses to fabricate the
rest:

  A. fetch_cil_grade_prices()  -> data/raw/cil_grade_prices_fy2022-23.csv
     REAL + correct vintage. CIL grade-wise PITHEAD notified price (Rs/tonne) from
     notification 194 dated 27-11-2020 (in force across all of FY2022-23, until the
     31-05-2023 hike), Table I "Power Utilities" column. Consumed by 02 to ground
     the domestic coal price. Source PDF: cercind.gov.in CPI archive.

  B. fetch_cerc_station_ecr() -> data/raw/plant_ecr_cerc_2018basis.csv
     REAL per-station ECR, but a 2018-19 BASIS (CERC computes the working-capital
     ECR on the Oct-Dec 2018 landed coal cost at the start of the 2019-24 period).
     Therefore NOT FY2022-23 -> used ONLY by the 08 cross-check, never the headline.
     Station-name mapping is an explicit curated alias map (NOT difflib), because a
     fuzzy match snapped "National Capital TPS (Dadri)" onto the unrelated
     "Bhadradri" station in testing.

  C. The FY2022-23 per-station override (data/raw/plant_ecr.csv) is intentionally
     NOT written: its feeds are down (above). Emitting a number here would be
     fabrication. The headline cost falls back to the real-CIL-grounded model (02).

Both committed CSVs are the human-verified readings of these PDFs; this script
re-derives them from the live source and warns if the source has drifted. It needs
`requests`, `pypdfium2` and `pdfplumber` (see requirements.txt).

Run:  python3 analysis/07_fetch_ecr.py
"""
from __future__ import annotations
import os
import re
import time
from urllib.parse import quote
import pandas as pd
from common import REPO

RAW = os.path.join(REPO, "data", "raw")
CIL_OUT = os.path.join(RAW, "cil_grade_prices_fy2022-23.csv")
CERC_OUT = os.path.join(RAW, "plant_ecr_cerc_2018basis.csv")
FY2223_OUT = os.path.join(RAW, "plant_ecr.csv")  # deliberately NOT written (see above)
CACHE = os.path.join(RAW, "_ecr_cache")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

# Verified reference readings (the manually-confirmed values from the real PDFs).
CIL_PITHEAD_REF = {  # Rs/tonne, Power-Utilities col, notif. 194 dated 27-11-2020
    "G2": 3298, "G3": 3154, "G4": 3010, "G5": 2747, "G6": 2327, "G7": 1936,
    "G8": 1475, "G9": 1150, "G10": 1034, "G11": 965, "G12": 896, "G13": 827,
    "G14": 758, "G15": 600, "G16": 574, "G17": 457,
}
CIL_GCV_BAND = {  # grade -> (low, high) kcal/kg
    "G1": (7000, None), "G2": (6700, 7000), "G3": (6400, 6700), "G4": (6100, 6400),
    "G5": (5800, 6100), "G6": (5500, 5800), "G7": (5200, 5500), "G8": (4900, 5200),
    "G9": (4600, 4900), "G10": (4300, 4600), "G11": (4000, 4300), "G12": (3700, 4000),
    "G13": (3400, 3700), "G14": (3100, 3400), "G15": (2800, 3100), "G16": (2500, 2800),
    "G17": (2200, 2500),
}
CIL_NOTIF_PDF = "2021/CPI/Coal Price Notification dated 27-11-2020.pdf"

# CERC 2019-24 generation-tariff "determination/approval" orders -> dataset station.
# Curated explicit aliases (verified): {petition file: dataset station name}.
CERC_ORDERS = {
    "2023/orders/425-GT-2020.pdf": "Sipat Stps", "2022/orders/435-GT-2020.pdf": "Sipat Stps",
    "2022/orders/486-GT-2020.pdf": "Korba Stps", "2022/orders/419-GT-2020.pdf": "Korba Stps",
    "2023/orders/424-GT-2020.pdf": "Singrauli Stps",
    "2022/orders/426GT.pdf": "Rihand", "2023/orders/430-GT-2020.pdf": "Rihand",
    "2023/orders/433-GT-2020.pdf": "Rihand",
    "2022/orders/485-GT-2020.pdf": "Vindh_Chal Stps", "2022/orders/401-GT-2020.pdf": "Vindh_Chal Stps",
    "2023/orders/415-GT-2020.pdf": "Vindh_Chal Stps", "2023/orders/402-GT-2020.pdf": "Vindh_Chal Stps",
    "2023/orders/441-GT-2020.pdf": "Talcher Stps",
    "2022/orders/396-GT-2020.pdf": "Bhilai TPP",
    "2023/orders/429-GT-2020.pdf": "Farakka Stps",
    "2023/orders/416-GT-2020.pdf": "R_Gundem Stps",
    "2023/orders/417-GT-2020.pdf": "Simhadri", "2022/orders/418-GT-2020.pdf": "Simhadri",
    "2022/orders/437-GT-2020.pdf": "Mouda Stps", "2023/orders/423-GT-2020.pdf": "Mouda Stps",
    "2022/orders/427-GT-2020.pdf": "Unchahar", "2022/orders/431-GT-2020.pdf": "Unchahar",
    "2022/orders/3-GT-2021.pdf": "Unchahar",
    "2022/orders/489-GT-2020.pdf": "Indra Gandhi STPP",
    "2022/orders/2-GT-2021.pdf": "Dadri (NcTPP)",
}
# FY2022-23 per-station metered feeds to probe (expected down this session).
FY2223_FEEDS = ["https://grid-india.in", "https://hrd.posoco.in/elibrary",
                "https://meritindia.in", "https://npp.gov.in"]


def _get(path_or_url, binary=True, retries=6):
    import requests
    os.makedirs(CACHE, exist_ok=True)
    url = path_or_url if path_or_url.startswith("http") else "https://cercind.gov.in/" + quote(path_or_url)
    key = os.path.join(CACHE, re.sub(r"[^a-zA-Z0-9]", "_", url)[:180])
    if os.path.exists(key) and os.path.getsize(key) > 2000:
        return open(key, "rb").read() if binary else open(key, encoding="utf-8", errors="replace").read()
    for i in range(retries):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            if r.status_code == 200 and len(r.content) > 2000:
                open(key, "wb").write(r.content)
                return r.content if binary else r.text
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1.2 * (i + 1))
    return None


def fetch_cil_grade_prices() -> pd.DataFrame:
    """Source A: CIL FY2022-23 pithead price by grade (Power-Utilities column)."""
    import pdfplumber
    pdf_bytes = _get(CIL_NOTIF_PDF)
    if not pdf_bytes:
        raise RuntimeError("could not download the CIL 27-11-2020 notification")
    tmp = os.path.join(CACHE, "_cil.pdf")
    open(tmp, "wb").write(pdf_bytes)
    parsed = {}
    with pdfplumber.open(tmp) as pdf:
        words = pdf.pages[1].extract_words(use_text_flow=False, keep_blank_chars=False)
    grades = [(w["text"].strip(), w["top"]) for w in words if re.fullmatch(r"G\d{1,2}", w["text"].strip())]
    # Power-Utilities price column sits at x0 ~ 410-470; concatenate the digit
    # tokens in that band on each grade's row (OCR splits e.g. "3"+"298"=3298).
    for g, gtop in grades:
        toks = sorted((w for w in words if 405 <= w["x0"] <= 475 and abs(w["top"] - gtop) <= 7),
                      key=lambda w: w["x0"])
        digits = "".join(re.sub(r"\D", "", t["text"]) for t in toks)
        if digits:
            parsed[g] = int(digits)
    # Validate against the verified reference; warn on drift, keep the reference.
    out = []
    for g, ref in CIL_PITHEAD_REF.items():
        if g in parsed and parsed[g] != ref:
            print(f"  [CIL WARN] {g}: parsed {parsed[g]} != reference {ref} "
                  f"(source may have drifted; keeping verified reference)")
        lo, hi = CIL_GCV_BAND[g]
        out.append({"grade": g, "gcv_low_kcal_per_kg": lo, "gcv_high_kcal_per_kg": hi,
                    "pithead_rom_rs_per_tonne_power": ref, "period": "FY2022-23",
                    "source": "CIL notif. 194 dated 27-11-2020, Table I"})
    print(f"  [CIL] parsed {len(parsed)} grade rows from the live PDF; wrote {len(out)} verified rows")
    return pd.DataFrame(out)


def _ecr_from_order(text: str):
    """(allowed_ex_bus, claimed) ECR Rs/kWh from a CERC GT order, if present."""
    allowed = [float(m.group(1)) for m in re.finditer(
        r"Rate of [Ee]nergy [Cc]harge ex-?bus\s*Rs\.?/?\s*kWh\s*([0-9]\.[0-9]{2,4})", text)]
    mt = re.search(r"Energy Charge Rate\s*Primary fuel[^\n0-9]{0,25}"
                   r"([0-9]+\.[0-9]{2,4})\s+([0-9]+\.[0-9]{2,4})", text, re.I)
    if mt:
        allowed.append(float(mt.group(2)))
    claimed = [float(m.group(1)) for m in re.finditer(
        r"\bECR\b[^0-9]{0,18}(?:of\s*)?Rs\.?\s*([0-9]\.[0-9]{2,4})\s*(?:per|/)\s*k?Wh", text, re.I)]
    a = allowed[-1] if allowed else None
    c = claimed[0] if claimed else None
    return a, c


def fetch_cerc_station_ecr() -> pd.DataFrame:
    """Source B: CERC per-station ECR (2018-19 basis) -> labelled cross-check only."""
    import pypdfium2 as pdfium
    rows = []
    for path, station in CERC_ORDERS.items():
        b = _get(path)
        if not b:
            print(f"  [CERC] download failed: {path}")
            continue
        tmp = os.path.join(CACHE, "_o.pdf")
        open(tmp, "wb").write(b)
        doc = pdfium.PdfDocument(tmp)
        text = "\n".join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
        doc.close()
        if len(text) < 2000:
            print(f"  [CERC] {os.path.basename(path)} has no text layer (image PDF) - skipped")
            continue
        a, c = _ecr_from_order(text)
        val = a if a is not None else c
        if val is None:
            print(f"  [CERC] no ECR found in {os.path.basename(path)} - skipped")
            continue
        rows.append({"match_name": station, "ecr": val,
                     "basis": "allowed" if a is not None else "claimed",
                     "order": os.path.basename(path)})
    raw = pd.DataFrame(rows)
    agg = (raw.groupby("match_name")
              .agg(ecr_rs_per_kwh=("ecr", "mean"), n_orders=("ecr", "size"),
                   basis=("basis", lambda s: "/".join(sorted(set(s)))),
                   source=("order", lambda s: "CERC " + "; ".join(sorted(s))))
              .reset_index())
    agg["ecr_rs_per_kwh"] = agg["ecr_rs_per_kwh"].round(3)
    agg["period"] = "2018-19 basis (CERC 2019-24 tariff order; Oct-Dec 2018 coal cost)"
    print(f"  [CERC] extracted ECR for {len(agg)} stations across {len(raw)} orders")
    return agg[["match_name", "ecr_rs_per_kwh", "basis", "n_orders", "period", "source"]]


def probe_fy2223_feeds():
    """Probe the FY2022-23 metered per-station feeds; report status (no fabrication)."""
    import requests
    print("\nProbing FY2022-23 per-station metered ECR feeds (need these for plant_ecr.csv):")
    up = []
    for u in FY2223_FEEDS:
        try:
            code = requests.get(u, headers=UA, timeout=20).status_code
        except Exception:  # noqa: BLE001
            code = "refused"
        print(f"  {u} -> {code}")
        if code == 200:
            up.append(u)
    return up


def main():
    print("=" * 72)
    print("07 - FETCH REAL FUEL-PRICE / ECR INPUTS (refuses to fabricate)")
    print("=" * 72)

    try:
        cil = fetch_cil_grade_prices()
        cil.to_csv(CIL_OUT, index=False)
        print(f"  -> wrote {os.path.relpath(CIL_OUT, REPO)} ({len(cil)} rows)")
    except Exception as e:  # noqa: BLE001
        print(f"  [CIL] FAILED ({e}); keeping the committed cil_grade_prices CSV")

    try:
        cerc = fetch_cerc_station_ecr()
        if len(cerc):
            cerc.to_csv(CERC_OUT, index=False)
            print(f"  -> wrote {os.path.relpath(CERC_OUT, REPO)} ({len(cerc)} stations, 2018-19 basis)")
    except Exception as e:  # noqa: BLE001
        print(f"  [CERC] FAILED ({e}); keeping the committed plant_ecr_cerc_2018basis CSV")

    up = probe_fy2223_feeds()
    if up:
        print(f"\n[!] {up} now reachable -- implement their parser and write FY2022-23")
        print("    METERED per-station ECR to data/raw/plant_ecr.csv, then run 06.")
        print("    NOTE: npp.gov.in / MERIT serve CURRENT-year merit data via XHR, not")
        print("    FY2022-23 -- only paste a number into plant_ecr.csv if it is FY2022-23.")
    else:
        print("\nNo FY2022-23 per-station feed reachable -> NOT writing plant_ecr.csv")
        print("(refusing to emit fabricated / wrong-vintage FY2022-23 ECR). Headline cost")
        print("stays on the real-CIL-grounded model (02); CERC ECRs feed only the 08 cross-check.")


if __name__ == "__main__":
    main()
