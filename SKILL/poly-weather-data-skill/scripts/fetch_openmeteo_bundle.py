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
    parser.add_argument("--model", required=True)
    parser.add_argument("--history-start", required=True)
    parser.add_argument("--history-end", required=True)
    parser.add_argument("--forecast-hours", type=int, default=24)
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    common = {
        "latitude": args.latitude, "longitude": args.longitude, "models": args.model,
        "hourly": ",".join(VARIABLES), "timezone": args.timezone,
    }
    history_url = "https://historical-forecast-api.open-meteo.com/v1/forecast?" + urlencode({
        **common, "start_date": args.history_start, "end_date": args.history_end,
    })
    forecast_url = "https://api.open-meteo.com/v1/forecast?" + urlencode({
        **common, "forecast_hours": args.forecast_hours,
    })
    fetched_at = datetime.now(timezone.utc).isoformat()
    summary = {"airport_icao": args.icao, "model_requested": args.model, "fetched_at_utc": fetched_at, "requests": {}}
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
