#!/usr/bin/env python3
"""Fetch one explicit Open-Meteo model for a historical and future weather bundle."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

VARIABLES = [
    "temperature_2m", "precipitation", "rain", "cloud_cover", "cloud_cover_low",
    "cloud_cover_mid", "cloud_cover_high", "weather_code",
]

MODEL_CATALOG = {
    "ecmwf_ifs": {"job": 2, "display_name": "ECMWF IFS HRES", "provider_family": "ECMWF_IFS", "series_type": "deterministic"},
    "ecmwf_aifs025_single": {"job": 3, "display_name": "ECMWF AIFS 0.25° Single", "provider_family": "ECMWF_AIFS", "series_type": "deterministic_ai"},
    "gfs_seamless": {"job": 4, "display_name": "NOAA GFS", "provider_family": "NOAA_GFS", "series_type": "seamless"},
    "icon_seamless": {"job": 5, "display_name": "DWD ICON", "provider_family": "DWD_ICON", "series_type": "seamless"},
    "best_match": {"job": 6, "display_name": "best_match", "provider_family": "AUTOMATIC", "series_type": "automatic_non_fixed"},
    "dwd_icon_global": {"job": 7, "display_name": "DWD ICON Global", "provider_family": "DWD_ICON", "series_type": "deterministic"},
    "ncep_gfs_global": {"job": 8, "display_name": "NOAA GFS Global", "provider_family": "NOAA_GFS", "series_type": "deterministic"},
    "ecmwf_ifs025": {"job": 9, "display_name": "ECMWF IFS 0.25°", "provider_family": "ECMWF_IFS", "series_type": "deterministic"},
    "arpege_world": {"job": 10, "display_name": "Météo-France ARPEGE World", "provider_family": "METEO_FRANCE_ARPEGE", "series_type": "deterministic"},
    "ukmo_global_deterministic_10km": {"job": 11, "display_name": "UKMO Global", "provider_family": "UKMO", "series_type": "deterministic"},
    "jma_gsm": {"job": 12, "display_name": "JMA GSM", "provider_family": "JMA", "series_type": "deterministic"},
    "gem_global": {"job": 13, "display_name": "Canadian GEM Global", "provider_family": "ECCC_GEM", "series_type": "deterministic"},
    "cma_grapes_global": {"job": 14, "display_name": "CMA GFS GRAPES", "provider_family": "CMA_GRAPES", "series_type": "deterministic"},
    "ncep_aigfs025": {"job": 15, "display_name": "NOAA AIGFS", "provider_family": "NOAA_AIGFS", "series_type": "deterministic_ai"},
    "ncep_hgefs025_ensemble_mean": {"job": 16, "display_name": "NOAA HGEFS ensemble mean", "provider_family": "NOAA_HGEFS", "series_type": "ensemble_mean"},
}


def fetch(url: str) -> dict:
    with urlopen(url, timeout=60) as response:  # nosec B310: fixed trusted Open-Meteo host
        body = response.read()
    return json.loads(body.decode("utf-8"))


def quality(payload: dict) -> dict:
    hourly = payload.get("hourly", {})
    output = {}
    for variable in VARIABLES:
        values = hourly.get(variable, [])
        non_null = sum(value is not None for value in values)
        output[variable] = {
            "returned_points": len(values),
            "non_null_points": non_null,
            "coverage_ratio": round(non_null / len(values), 4) if values else 0,
            "status": "available" if values and non_null == len(values) else "data_unavailable" if non_null == 0 else "partial",
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--icao", required=True)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--model", required=True, choices=sorted(MODEL_CATALOG))
    parser.add_argument("--history-start", required=True)
    parser.add_argument("--history-end", required=True)
    parser.add_argument("--forecast-hours", type=int, default=24)
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_metadata = MODEL_CATALOG[args.model]
    common = {
        "latitude": args.latitude, "longitude": args.longitude,
        "hourly": ",".join(VARIABLES), "timezone": args.timezone,
    }
    if args.model != "best_match":
        common["models"] = args.model
    history_url = "https://historical-forecast-api.open-meteo.com/v1/forecast?" + urlencode({
        **common, "start_date": args.history_start, "end_date": args.history_end,
    })
    forecast_url = "https://api.open-meteo.com/v1/forecast?" + urlencode({
        **common, "forecast_hours": args.forecast_hours,
    })
    fetched_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "airport_icao": args.icao,
        "model_requested": args.model,
        "models_parameter_sent": args.model != "best_match",
        "model_catalog_metadata": model_metadata,
        "fetched_at_utc": fetched_at,
        "governance": {
            "null_policy": "A missing series is recorded as data_unavailable and never filled from another model.",
            "independence_policy": "Provider-family related series are retained separately and must not be treated as independent evidence.",
            "best_match_policy": "Automatic routing is collected only as job 6 and never as an implicit fallback.",
        },
        "requests": {},
    }
    for name, url in (("history", history_url), ("forecast", forecast_url)):
        payload = fetch(url)
        raw_path = out_dir / f"{args.icao}_{args.model}_{name}_raw.json"
        raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        summary["requests"][name] = {
            "url": url,
            "raw_file": raw_path.name,
            "sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
            "response_coordinate": {key: payload.get(key) for key in ("latitude", "longitude", "elevation")},
            "timezone": payload.get("timezone"),
            "utc_offset_seconds": payload.get("utc_offset_seconds"),
            "units": payload.get("hourly_units"),
            "variables": quality(payload),
        }
    (out_dir / f"{args.icao}_{args.model}_quality_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
