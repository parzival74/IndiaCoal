"""
Fetch the data.gov.in 'Generating Station-wise Tariff Statement' datasets (real,
structured per-station Energy Charge Rate / ECR) and write a committed CSV.

These are Rajya Sabha parliamentary-answer annexures published on data.gov.in. They
carry per-station ECR (Rs/kWh) for CENTRAL / ISGS thermal stations, covering FY2021-22
(NTPC) and a 2021-23 window (NLC/DVC). They are the most contemporaneous REAL per-station
ECR we can reach (the genuinely FY2022-23 metered feeds -- MERIT/SCED/SLDC -- refuse from
this environment). VINTAGE CAVEAT: 2021-22 / 2021-23, ISGS-only -- NOT a clean FY2022-23,
and NO state/private generators. Used as a contemporaneous cross-check, not the headline.

NETWORK + KEY: needs a free data.gov.in API key in env var DATAGOVIN_API_KEY. The key is
NEVER written to disk or committed. Not part of run_all.py (the output CSV is committed,
so the offline pipeline -- analysis/10_datagov_ecr.py -- is reproducible without network).

Run:  DATAGOVIN_API_KEY=xxxx python3 analysis/fetch_datagov_ecr.py
Writes: data/raw/datagov_tariff_ecr_2021-23.csv
Source: https://www.data.gov.in/resource/<slug>  (resource IDs below)
"""
from __future__ import annotations
import os
import sys
import time
import json
import urllib.request
import urllib.error
import csv

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data", "raw", "datagov_tariff_ecr_2021-23.csv")
API = "https://api.data.gov.in/resource/{rid}?api-key={key}&format=json&limit=10&offset={off}"

# resource_id -> (short label, vintage as stated in the dataset title)
RESOURCES = {
    "9a0d4b8a-3581-4676-a834-da0b837385b4": ("NLC+DVC+gas", "2021-23"),
    "948ebec1-52eb-44d3-a97c-1761f8ad4c54": ("NTPC+JV", "2021-22"),
    "97d10fda-6480-4895-8754-2e041021f848": ("Central->Bihar", "2021-22"),
}


def get_json(url, tries=6):
    """GET with backoff on HTTP 429 (data.gov.in rate-limits)."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return json.load(urllib.request.urlopen(req, timeout=40))
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                wait = 5 * (2 ** i)
                print(f"  429 rate-limited; backing off {wait}s")
                time.sleep(wait)
                continue
            raise


def field_ids(meta):
    """The three datasets use slightly different column ids; resolve them robustly."""
    ids = {f["id"]: f.get("name", "") for f in meta.get("field", [])}
    def pick(*subs):
        for fid, name in ids.items():
            low = (fid + " " + name).lower()
            if all(s in low for s in subs):
                return fid
        return None
    return {
        "station": pick("name", "station") or pick("station") or pick("name"),
        "category": pick("category"),
        "ecr": pick("energy", "charge") or pick("ecr"),
        "nfc": pick("fixed", "charge"),
        "total": pick("total", "tariff"),
    }


def main():
    key = os.environ.get("DATAGOVIN_API_KEY")
    if not key:
        sys.exit("Set DATAGOVIN_API_KEY (free key from data.gov.in). The key is never "
                 "written to disk. Refusing to fetch without it.")

    rows = []
    for rid, (label, vintage) in RESOURCES.items():
        print(f"[{label}] {rid}  (vintage {vintage})")
        meta = get_json(API.format(rid=rid, key=key, off=0))
        total = int(meta.get("total", 0))
        title = meta.get("title", "")
        fids = field_ids(meta)
        recs = list(meta.get("records", []))
        off = 10
        while len(recs) < total:
            time.sleep(1.5)  # be gentle with the rate limiter
            recs += get_json(API.format(rid=rid, key=key, off=off)).get("records", [])
            off += 10
        for r in recs:
            cat = str(r.get(fids["category"], "") or label)
            station = r.get(fids["station"], "")
            ecr_raw = r.get(fids["ecr"])
            if ecr_raw in (None, ""):
                continue
            # Units: a category labelled 'Paise/KWh' (DVC) is in paise -> /100 to Rs/kWh.
            paise = "paise" in cat.lower()
            try:
                ecr_rs = float(ecr_raw) / (100.0 if paise else 1.0)
            except (TypeError, ValueError):
                continue
            rows.append({
                "resource_id": rid,
                "dataset_title": title,
                "vintage": vintage,
                "category": cat,
                "station_raw": str(station).strip(),
                "units_source": "paise/kWh" if paise else "Rs/kWh",
                "ecr_raw": ecr_raw,
                "ecr_rs_per_kwh": round(ecr_rs, 4),
                "nfc_raw": r.get(fids["nfc"]),
                "total_raw": r.get(fids["total"]),
            })
        print(f"  pulled {len(recs)}/{total} records")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cols = ["resource_id", "dataset_title", "vintage", "category", "station_raw",
            "units_source", "ecr_raw", "ecr_rs_per_kwh", "nfc_raw", "total_raw"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"\n[wrote {OUT}: {len(rows)} rows from {len(RESOURCES)} datasets]")


if __name__ == "__main__":
    main()
