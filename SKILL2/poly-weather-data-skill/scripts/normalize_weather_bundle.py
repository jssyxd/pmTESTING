#!/usr/bin/env python3
"""Normalize a fetch_weather_bundle.py output; preserve nulls and lineage.

Example:
  python normalize_weather_bundle.py --bundle ./weather_bundle
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def c_to_f(value: Any) -> int | None:
    return None if value is None else round(float(value) * 9 / 5 + 32)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def model_name(label: str) -> tuple[str, str]:
    if "_historical_" in label:
        return "historical_forecast", label.split("_historical_", 1)[1]
    return "forecast", label.split("_forecast_", 1)[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize a weather evidence bundle without interpolation.")
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    root, raw_dir, normal = args.bundle, args.bundle / "raw", args.bundle / "normalized"
    normal.mkdir(parents=True, exist_ok=True)
    manifest = load_json(root / "metadata" / "manifest.json")
    tz = ZoneInfo(str(manifest["timezone"]))
    anchor = datetime.fromisoformat(str(manifest["anchor_hour_local"]))
    hist_start = datetime.fromisoformat(str(manifest["history_window"]["start_inclusive"]))
    future_end = datetime.fromisoformat(str(manifest["future_window"]["end_inclusive"]))

    hourly_rows: list[dict[str, Any]] = []
    model_metadata: list[dict[str, Any]] = []
    metar_rows: list[dict[str, Any]] = []
    status_rows: list[dict[str, Any]] = []
    current_taf: dict[str, Any] | None = None

    for raw_file in sorted(raw_dir.glob("*.json")):
        evidence = load_json(raw_file)
        label, payload, status = str(evidence.get("label", "")), evidence.get("json"), evidence.get("status_code")
        status_rows.append({"label": label, "status_code": status, "captured_at_utc": evidence.get("captured_at_utc"), "request_url": evidence.get("request_url"), "raw_file": str(raw_file.relative_to(root)), "request_error": evidence.get("request_error")})
        if label.startswith("open_meteo_") and isinstance(payload, dict):
            segment, model = model_name(label)
            hourly = payload.get("hourly") or {}
            model_metadata.append({"label": label, "model_request": model, "segment": segment, "api_returned_latitude": payload.get("latitude"), "api_returned_longitude": payload.get("longitude"), "api_returned_elevation_m": payload.get("elevation"), "timezone": payload.get("timezone"), "timezone_abbreviation": payload.get("timezone_abbreviation"), "status_code": status, "captured_at_utc": evidence.get("captured_at_utc"), "request_url": evidence.get("request_url")})
            for index, text in enumerate(hourly.get("time") or []):
                when = datetime.fromisoformat(text).replace(tzinfo=tz)
                window = "history_72h" if segment == "historical_forecast" else "future_24h"
                include = hist_start <= when < anchor if window == "history_72h" else anchor < when <= future_end
                if not include:
                    continue
                def get(name: str) -> Any:
                    values = hourly.get(name) or []
                    return values[index] if index < len(values) else None
                temp = get("temperature_2m")
                hourly_rows.append({"time_local": when.isoformat(), "window": window, "segment": segment, "model_request": model, "temperature_2m_c": temp, "temperature_2m_f": c_to_f(temp), "precipitation_mm": get("precipitation"), "rain_mm": get("rain"), "cloud_cover_pct": get("cloud_cover"), "cloud_cover_low_pct": get("cloud_cover_low"), "cloud_cover_mid_pct": get("cloud_cover_mid"), "cloud_cover_high_pct": get("cloud_cover_high"), "retrieved_at_utc": evidence.get("captured_at_utc"), "request_url": evidence.get("request_url")})
        elif label == "awc_metar_72h" and isinstance(payload, list):
            for message in payload:
                if not isinstance(message, dict):
                    continue
                try:
                    when = datetime.fromtimestamp(float(message["obsTime"]), timezone.utc).astimezone(tz)
                except (KeyError, TypeError, ValueError, OSError):
                    continue
                if not hist_start <= when < anchor:
                    continue
                layers = message.get("clouds") if isinstance(message.get("clouds"), list) else []
                temp = message.get("temp")
                metar_rows.append({"observation_time_local": when.isoformat(), "temperature_c": temp, "temperature_f": c_to_f(temp), "precipitation_mm": message.get("precip"), "cloud_cover_code": message.get("cover"), "cloud_layers": "; ".join(f"{x.get('cover')}@{x.get('base')}ft" for x in layers if isinstance(x, dict)) or None, "weather_text": message.get("wxString"), "raw_metar": message.get("rawOb"), "station_latitude": message.get("lat"), "station_longitude": message.get("lon"), "station_elevation_m": message.get("elev"), "report_time_utc": message.get("reportTime"), "retrieved_at_utc": evidence.get("captured_at_utc"), "request_url": evidence.get("request_url")})
        elif label == "awc_current_taf" and isinstance(evidence.get("response_text"), str):
            raw_taf = str(evidence["response_text"]).strip()
            extrema = []
            for match in re.finditer(r"\b(TX|TN)(M?\d{2})/(\d{4})Z", raw_taf):
                raw_temp = match.group(2)
                celsius = -int(raw_temp[1:]) if raw_temp.startswith("M") else int(raw_temp)
                extrema.append({"kind": match.group(1), "temperature_c": celsius, "temperature_f": c_to_f(celsius), "day_hour_utc": match.group(3)})
            current_taf = {"status_code": status, "retrieved_at_utc": evidence.get("captured_at_utc"), "request_url": evidence.get("request_url"), "raw_taf": raw_taf, "tx_tn": extrema}

    hourly_rows.sort(key=lambda row: (row["model_request"], row["window"], row["time_local"]))
    metar_rows.sort(key=lambda row: row["observation_time_local"], reverse=True)
    fields = ["time_local", "window", "segment", "model_request", "temperature_2m_c", "temperature_2m_f", "precipitation_mm", "rain_mm", "cloud_cover_pct", "cloud_cover_low_pct", "cloud_cover_mid_pct", "cloud_cover_high_pct", "retrieved_at_utc", "request_url"]
    write_csv(normal / "open_meteo_hourly.csv", hourly_rows, fields)
    write_csv(normal / "open_meteo_model_metadata.csv", model_metadata, list(model_metadata[0].keys()) if model_metadata else ["label"])
    write_csv(normal / "awc_metar_actual_observations.csv", metar_rows, list(metar_rows[0].keys()) if metar_rows else ["observation_time_local"])
    write_csv(normal / "request_status.csv", status_rows, list(status_rows[0].keys()) if status_rows else ["label"])

    models: dict[str, Any] = {}
    for model in sorted({str(row["model_request"]) for row in hourly_rows}):
        hist = [row for row in hourly_rows if row["model_request"] == model and row["window"] == "history_72h"]
        future = [row for row in hourly_rows if row["model_request"] == model and row["window"] == "future_24h"]
        models[model] = {"history_rows": len(hist), "history_expected": 72, "future_rows": len(future), "future_expected": 24, "history_complete": len(hist) == 72, "future_complete": len(future) == 24, "null_temperature_rows": sum(x["temperature_2m_c"] is None for x in hist + future), "null_precipitation_rows": sum(x["precipitation_mm"] is None for x in hist + future), "null_cloud_rows": sum(x["cloud_cover_pct"] is None for x in hist + future)}
    coverage = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "timezone": str(manifest["timezone"]), "anchor_hour_local": anchor.isoformat(), "history_window": manifest["history_window"], "future_window": manifest["future_window"], "models": models, "metar": {"actual_observation_rows": len(metar_rows), "numeric_precipitation_rule": "null unless raw AWC JSON supplies precip", "cloud_rule": "METAR layers are categorical and are not converted to percent"}, "taf": {"current": current_taf, "history_72h_status": "not_collected_by_current_AWC_endpoint", "history_72h_rule": "use Ogimet range query or another archival source; report null if no raw historical TAF is returned"}, "weather_underground": {"status": "requires_rendered_page_adapter", "cloud_cover_pct_rule": "null when the WU table provides no numeric cloud cover"}}
    (normal / "coverage_report.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(normal), "hourly_rows": len(hourly_rows), "metar_rows": len(metar_rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
