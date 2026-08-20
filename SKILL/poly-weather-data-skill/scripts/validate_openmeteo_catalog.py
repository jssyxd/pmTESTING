#!/usr/bin/env python3
"""Independently validate all controlled Open-Meteo jobs for one airport/window."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from fetch_openmeteo_bundle import MODEL_CATALOG, VARIABLES, quality


def get_json(url: str) -> tuple[int | None, dict | None, str | None]:
    try:
        with urlopen(url, timeout=90) as response:  # nosec B310: fixed trusted Open-Meteo endpoints
            return response.status, json.loads(response.read().decode("utf-8")), None
    except HTTPError as error:
        return error.code, None, f"HTTPError: {error.reason}"
    except URLError as error:
        return None, None, f"URLError: {error.reason}"


def endpoint(base: str, common: dict[str, str | float], start: str | None, end: str | None, hours: int | None) -> str:
    query = dict(common)
    if start and end:
        query.update({"start_date": start, "end_date": end})
    if hours:
        query["forecast_hours"] = hours
    return f"{base}?{urlencode(query)}"


def record(url: str, response_status: int | None, payload: dict | None, error: str | None, expected_rows: int) -> dict:
    hourly = payload.get("hourly", {}) if payload else {}
    row_count = len(hourly.get("time", []))
    variable_quality = quality(payload) if payload else {
        variable: {"returned_points": 0, "non_null_points": 0, "coverage_ratio": 0, "status": "data_unavailable"}
        for variable in VARIABLES
    }
    target_complete = all(item["status"] == "available" for item in variable_quality.values()) and row_count == expected_rows
    return {
        "url": url,
        "http_status": response_status,
        "error": error,
        "returned_hour_rows": row_count,
        "expected_hour_rows": expected_rows,
        "target_variables_complete": target_complete,
        "response_coordinate": {key: payload.get(key) for key in ("latitude", "longitude", "elevation")} if payload else None,
        "timezone": payload.get("timezone") if payload else None,
        "utc_offset_seconds": payload.get("utc_offset_seconds") if payload else None,
        "variables": variable_quality,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--icao", required=True)
    parser.add_argument("--latitude", required=True, type=float)
    parser.add_argument("--longitude", required=True, type=float)
    parser.add_argument("--history-start", required=True)
    parser.add_argument("--history-end", required=True)
    parser.add_argument("--forecast-hours", default=24, type=int)
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    output = {
        "airport_icao": args.icao,
        "request_coordinate": {"latitude": args.latitude, "longitude": args.longitude},
        "history_window": {"start_date": args.history_start, "end_date": args.history_end, "expected_hour_rows": 72},
        "forecast_window": {"forecast_hours": args.forecast_hours},
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_results": [],
        "governance": "Each job is requested separately. Failure, partial coverage or null arrays remain data_unavailable; no sibling or automatic model is used for fill.",
    }
    for model_id, metadata in sorted(MODEL_CATALOG.items(), key=lambda item: item[1]["job"]):
        common = {
            "latitude": args.latitude,
            "longitude": args.longitude,
            "hourly": ",".join(VARIABLES),
            "timezone": args.timezone,
        }
        if model_id != "best_match":
            common["models"] = model_id
        history_url = endpoint("https://historical-forecast-api.open-meteo.com/v1/forecast", common, args.history_start, args.history_end, None)
        forecast_url = endpoint("https://api.open-meteo.com/v1/forecast", common, None, None, args.forecast_hours)
        history_status, history_payload, history_error = get_json(history_url)
        forecast_status, forecast_payload, forecast_error = get_json(forecast_url)
        output["catalog_results"].append({
            "job": metadata["job"],
            "model_id": model_id,
            "display_name": metadata["display_name"],
            "provider_family": metadata["provider_family"],
            "series_type": metadata["series_type"],
            "models_parameter_sent": model_id != "best_match",
            "history": record(history_url, history_status, history_payload, history_error, 72),
            "forecast": record(forecast_url, forecast_status, forecast_payload, forecast_error, args.forecast_hours),
        })
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
