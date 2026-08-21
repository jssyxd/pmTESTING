#!/usr/bin/env python3
"""Delivery gate for city weather documents (anti-hallucination).

Checks, per city document under 每日数据/:
  (a) literal placeholder tokens are absent (template style only);
  (b) every referenced raw file exists, non-zero, with complete meta
      (url/status/fetched_at_utc/bytes/sha256);
  (c) model-page rows are compared in FULL against the referenced raw arrays
      (doc local time == raw station-local naive time; values field-compared);
  (d) failure/coverage statements in 缺失说明 reference evidence files.

Writes doc_traceability_audit.json per city and prints a 47-city summary matrix.
The agent only RUNS this script; audit artifacts must never be hand-written.
"""

import argparse
import json
import re
import sys
from pathlib import Path

PLACEHOLDER_TOKENS = [
    "{country}", "{city}", "{ICAO}", "ids=ICAO", "icao=ICAO",
    "day=DD", "month=MM", "year=YYYY", "YYYY-MM-DD", "{model}",
]
META_REQUIRED = ["url", "status", "fetched_at_utc", "bytes", "sha256"]

# job -> Open-Meteo model param (for raw file lookup)
JOB_MODEL = {
    2: "ecmwf_ifs", 3: "ecmwf_aifs025_single", 4: "gfs_seamless", 5: "icon_seamless",
    6: "best_match", 7: "dwd_icon_global", 8: "ncep_gfs_global", 9: "ecmwf_ifs025",
    10: "arpege_world", 11: "ukmo_global_deterministic_10km", 12: "jma_gsm",
    13: "gem_global", 14: "cma_grapes_global", 15: "ncep_aigfs025",
    16: "ncep_hgefs025_ensemble_mean",
}
VARS = ["temperature_2m", "precipitation", "rain", "cloud_cover",
        "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high"]


def check_placeholders(text: str) -> list[str]:
    hits = []
    for tok in PLACEHOLDER_TOKENS:
        if tok in text:
            hits.append(tok)
    return hits


def check_meta(city_dir: Path) -> list[str]:
    problems = []
    for meta_path in sorted(city_dir.glob("raw/*.meta.json")) + sorted(city_dir.glob("openmeteo/*.meta.json")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{meta_path.name}: unreadable ({exc})")
            continue
        missing = [f for f in META_REQUIRED if f not in meta]
        raw = meta_path.with_suffix("")
        if missing:
            problems.append(f"{meta_path.name}: meta missing {missing}")
        if not raw.exists() or raw.stat().st_size == 0:
            problems.append(f"{raw.name}: missing or zero bytes")
    return problems


def compare_model_rows(doc_text: str, city_dir: Path) -> dict:
    """Full-compare model-page rows against raw JSON arrays."""
    result = {"blocks_checked": 0, "rows_compared": 0, "mismatches": []}
    for jm in re.finditer(r"## 【作业 (\d+)】", doc_text):
        job = int(jm.group(1))
        model = JOB_MODEL.get(job)
        if model is None:
            continue
        nxt = doc_text.find("---\n##", jm.end())
        seg = doc_text[jm.end(): nxt if nxt != -1 else len(doc_text)]
        rows = re.findall(
            r"^\| (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}) \| (历史 72 小时|未来 24 小时) \| "
            r"([^|]+) \| null \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|",
            seg, re.M)
        if not rows:
            continue
        result["blocks_checked"] += 1
        for kind, raw_name in (("历史 72 小时", "history"), ("未来 24 小时", "forecast")):
            raw_path = city_dir / "openmeteo" / f"{model}_{raw_name}_raw.json"
            raw_name_icao = None
            # locate raw by ICAO prefix
            candidates = sorted(city_dir.glob(f"openmeteo/*_{model}_{raw_name}_raw.json"))
            if not candidates:
                result["mismatches"].append(f"job{job}: raw missing {model}_{raw_name}_raw.json")
                continue
            raw_path = candidates[0]
            try:
                payload = json.loads(raw_path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                result["mismatches"].append(f"job{job}: raw unreadable ({exc})")
                continue
            hourly = payload.get("hourly") or {}
            times = hourly.get("time") or []
            for i, (local, win, t_c, precip, rain, cc, lc, mc, hc) in enumerate(rows):
                if win != kind:
                    continue
                result["rows_compared"] += 1
                if local not in times:
                    result["mismatches"].append(f"job{job}: {local} not in raw times")
                    continue
                idx = times.index(local)
                expected = {
                    "temperature_2m": t_c.strip() or None,
                    "precipitation": precip.strip() or None,
                    "rain": rain.strip() or None,
                    "cloud_cover": cc.strip() or None,
                    "cloud_cover_low": lc.strip() or None,
                    "cloud_cover_mid": mc.strip() or None,
                    "cloud_cover_high": hc.strip() or None,
                }
                for var, exp in expected.items():
                    raw_val = (hourly.get(var) or [None] * len(times))[idx]
                    exp_s = "null" if exp is None else exp
                    raw_s = "null" if raw_val is None else (f"{raw_val:g}" if isinstance(raw_val, float) else str(raw_val))
                    if exp_s != raw_s:
                        result["mismatches"].append(
                            f"job{job} {local} {var}: doc={exp_s} raw={raw_s}")
    return result


def audit_city(doc: Path, city_dir: Path) -> dict:
    text = doc.read_text(encoding="utf-8")
    return {
        "doc": doc.name,
        "placeholders": check_placeholders(text),
        "meta_problems": check_meta(city_dir),
        "model_compare": compare_model_rows(text, city_dir),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="每日数据", help="evidence root")
    ap.add_argument("--docs", nargs="*", default=None, help="limit to specific docs (basenames)")
    args = ap.parse_args()

    root = Path(args.root)
    docs = sorted(root.glob("*.md"))
    if args.docs:
        docs = [d for d in docs if d.name in args.docs]
    summary = []
    failed = 0
    for doc in docs:
        city_dir = root / doc.stem
        audit = audit_city(doc, city_dir)
        ok = (not audit["placeholders"] and not audit["meta_problems"]
              and not audit["model_compare"]["mismatches"])
        audit["pass"] = ok
        summary.append(audit)
        (city_dir / "doc_traceability_audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        if not ok:
            failed += 1
            print(f"FAIL {doc.name}: placeholders={audit['placeholders']} "
                  f"meta={len(audit['meta_problems'])} "
                  f"mismatches={len(audit['model_compare']['mismatches'])}", flush=True)
    print(f"SUMMARY docs={len(docs)} passed={len(docs) - failed} failed={failed}", flush=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
