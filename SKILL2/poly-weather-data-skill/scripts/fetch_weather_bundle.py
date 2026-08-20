#!/usr/bin/env python3
"""Fetch auditable weather evidence without interpolation.

Example:
  python fetch_weather_bundle.py --icao ZGGG --lat 23.3933 --lon 113.3083 \
    --timezone Asia/Shanghai --out ./weather_bundle
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import requests

HOURLY = ["temperature_2m", "precipitation", "rain", "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high"]
# First five preserve the original homework set. The remaining explicit identifiers cover
# additional global providers listed in the workbook. Keep each response separate; never
# use another model to fill a failed or all-null model.
MODELS = [
    "ecmwf_ifs", "ecmwf_aifs025_single", "gfs_seamless", "icon_seamless", "best_match",
    "dwd_icon_global", "ncep_gfs_global", "ecmwf_ifs04", "ecmwf_ifs025",
    "arpege_world", "ukmo_global_deterministic_10km", "jma_gsm", "gem_global",
    "bom_access_global", "cma_grapes_global", "ncep_aigfs025", "ncep_hgefs025_ensemble_mean",
]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def request_evidence(session: requests.Session, raw_dir: Path, label: str, url: str, params: dict[str, object]) -> dict[str, object]:
    """Request once and preserve both errors and raw responses."""
    captured_at = iso_now()
    record: dict[str, object] = {
        "label": label, "captured_at_utc": captured_at, "url": url, "params": params,
        "request_url": f"{url}?{urlencode(params, doseq=True)}",
    }
    try:
        response = session.get(url, params=params, timeout=45)
        record["status_code"] = response.status_code
        record["response_headers"] = dict(response.headers)
        record["response_text"] = response.text
        if "json" in response.headers.get("content-type", "").lower():
            try:
                record["json"] = response.json()
            except ValueError as exc:
                record["json_parse_error"] = str(exc)
    except requests.RequestException as exc:
        record["status_code"] = None
        record["request_error"] = repr(exc)
    filename = f"{captured_at.replace(':', '').replace('-', '')}_{label}.json"
    write_json(raw_dir / filename, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch auditable raw evidence for an airport/coordinate, including original and workbook global models.")
    parser.add_argument("--icao", required=True)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--anchor-local", help="ISO local datetime; default is current local hour")
    args = parser.parse_args()

    local_tz = ZoneInfo(args.timezone)
    anchor = (datetime.fromisoformat(args.anchor_local).astimezone(local_tz) if args.anchor_local else datetime.now(local_tz)).replace(minute=0, second=0, microsecond=0)
    history_start, future_end = anchor - timedelta(hours=72), anchor + timedelta(hours=24)
    raw_dir, meta_dir = args.out / "raw", args.out / "metadata"
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "poly-weather-data-skill/1.0"
    records: list[dict[str, object]] = []
    for model in MODELS:
        common = {
            "latitude": args.lat, "longitude": args.lon, "hourly": ",".join(HOURLY), "timezone": args.timezone,
        }
        historical = {**common, "start_date": history_start.date().isoformat(), "end_date": anchor.date().isoformat()}
        forecast = {**common, "start_date": anchor.date().isoformat(), "end_date": future_end.date().isoformat()}
        if model != "best_match":
            historical["models"] = model
            forecast["models"] = model
        records.append(request_evidence(session, raw_dir, f"open_meteo_historical_{model}", "https://historical-forecast-api.open-meteo.com/v1/forecast", historical))
        time.sleep(0.4)
        records.append(request_evidence(session, raw_dir, f"open_meteo_forecast_{model}", "https://api.open-meteo.com/v1/forecast", forecast))
        time.sleep(0.4)

    records.append(request_evidence(session, raw_dir, "awc_metar_72h", "https://aviationweather.gov/api/data/metar", {"ids": args.icao, "format": "json", "taf": "false", "hours": 72}))
    time.sleep(0.4)
    # Current raw TAF supports job 1. Do not describe it as 72-hour historical issuance archive.
    records.append(request_evidence(session, raw_dir, "awc_current_taf", "https://aviationweather.gov/api/data/taf", {"ids": args.icao}))
    time.sleep(0.4)
    # IEM requires a network value; CN__ASOS is appropriate for ZGGG. Its non-US precipitation can be unavailable.
    records.append(request_evidence(session, raw_dir, "iem_cn_asos", "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", {
        "station": args.icao, "data": "all", "year1": history_start.year, "month1": history_start.month, "day1": history_start.day,
        "year2": anchor.year, "month2": anchor.month, "day2": anchor.day, "tz": "Etc/UTC", "format": "onlycomma",
        "latlon": "no", "elev": "no", "missing": "M", "trace": "T", "direct": "no", "report_type": [3, 4],
    }))
    manifest = {
        "icao": args.icao, "coordinate": {"latitude": args.lat, "longitude": args.lon}, "timezone": args.timezone,
        "captured_at_utc": iso_now(), "anchor_hour_local": anchor.isoformat(),
        "history_window": {"start_inclusive": history_start.isoformat(), "end_exclusive": anchor.isoformat(), "expected_hours": 72},
        "future_window": {"start_exclusive": anchor.isoformat(), "end_inclusive": future_end.isoformat(), "expected_hours": 24},
        "requests": [{"label": x["label"], "status_code": x.get("status_code"), "request_url": x["request_url"]} for x in records],
        "wu_urls": {
            "hourly": f"https://www.wunderground.com/hourly/cn/guangzhou/{args.icao}",
            "history_pattern": f"https://www.wunderground.com/history/daily/cn/guangzhou/{args.icao}/date/YYYY-M-D",
        },
    }
    write_json(meta_dir / "manifest.json", manifest)
    print(json.dumps({"output": str(args.out), "status_codes": [x.get("status_code") for x in records]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
