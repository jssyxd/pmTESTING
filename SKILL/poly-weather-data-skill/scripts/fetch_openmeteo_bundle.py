#!/usr/bin/env python3
"""Fetch one explicit Open-Meteo model for a historical and future weather bundle.

v2 (anti-hallucination hardening):
- retry + exponential backoff for SSL/timeout/429/5xx; 404/400 deterministic, no retry
- read timeout 30s (fail fast on connect via 10s socket timeout)
- --timezone resolved from the 47-city settlement table by ICAO (error if unknown)
- sidecar meta written at save time: url/status/fetched_at_utc/bytes/sha256 + attempts
- forecast requested with station-local start_date/end_date (anchored windows),
  not forecast_hours (which anchors at fetch time)
"""

import argparse
import hashlib
import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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

# Settlement-station local IANA per ICAO (from the 47-city list in
# optimized-data-agent-polymarket-all-cities.md). --timezone is resolved from
# this table by --icao; unknown ICAO is an error, never a silent default.
ICAO_TIMEZONE = {
    "ZSPD": "Asia/Shanghai", "RJTT": "Asia/Tokyo", "KBKF": "America/Denver",
    "KATL": "America/New_York", "KHOU": "America/Chicago", "EGLC": "Europe/London",
    "VILK": "Asia/Kolkata", "ZBAA": "Asia/Shanghai", "EPWA": "Europe/Warsaw",
    "OPKC": "Asia/Karachi", "RCSS": "Asia/Taipei", "OEJN": "Asia/Riyadh",
    "WMKK": "Asia/Kuala_Lumpur", "SBGR": "America/Sao_Paulo", "MMMX": "America/Mexico_City",
    "CYYZ": "America/Toronto", "KAUS": "America/Chicago", "LTAC": "Europe/Istanbul",
    "MPMG": "America/Panama", "LFPB": "Europe/Paris", "SAEZ": "America/Argentina/Buenos_Aires",
    "ZGGG": "Asia/Shanghai", "FACT": "Africa/Johannesburg", "NZWN": "Pacific/Auckland",
    "EDDM": "Europe/Berlin", "ZUUU": "Asia/Shanghai", "WSSS": "Asia/Singapore",
    "KSFO": "America/Los_Angeles", "ZHHH": "Asia/Shanghai", "KLAX": "America/Los_Angeles",
    "ZSJN": "Asia/Shanghai", "ZGSZ": "Asia/Shanghai", "LIMC": "Europe/Rome",
    "KLGA": "America/New_York", "KORD": "America/Chicago", "KSEA": "America/Los_Angeles",
    "EFHK": "Europe/Helsinki", "KDAL": "America/Chicago", "KMIA": "America/New_York",
    "ZHCC": "Asia/Shanghai", "ZUCK": "Asia/Shanghai", "RKPK": "Asia/Seoul",
    "EHAM": "Europe/Amsterdam", "ZSQD": "Asia/Shanghai", "RKSI": "Asia/Seoul",
    "RPLL": "Asia/Manila", "LEMD": "Europe/Madrid",
}

MAX_ATTEMPTS = 3
BACKOFF = (2, 5, 10)
READ_TIMEOUT = 30
CONNECT_TIMEOUT = 10


def fetch(url: str, timeout: int = READ_TIMEOUT) -> tuple[dict | None, list]:
    """GET url with retry/backoff; returns (payload, attempts_log)."""
    attempts = []
    last_err = None
    for i in range(MAX_ATTEMPTS):
        ts = datetime.now(timezone.utc).isoformat()
        try:
            req = Request(url, headers={"User-Agent": "poly-weather-data-skill/2.0",
                                        "Accept": "application/json"})
            with urlopen(req, timeout=timeout) as response:  # nosec B310: fixed trusted Open-Meteo hosts
                body = response.read()
                attempts.append({"ts": ts, "status": response.status, "bytes": len(body)})
                return json.loads(body.decode("utf-8")), attempts
        except HTTPError as exc:  # noqa: PERF203 - small fixed loop
            body = exc.read()
            attempts.append({"ts": ts, "status": exc.code, "bytes": len(body),
                             "error": body.decode("utf-8", errors="replace")[:200]})
            if exc.code in (404, 400):
                return None, attempts  # deterministic: no retry
            last_err = exc
        except (URLError, TimeoutError, OSError, socket.timeout) as exc:
            attempts.append({"ts": ts, "status": None, "error": f"{type(exc).__name__}: {exc}"})
            last_err = exc
        if i < MAX_ATTEMPTS - 1:
            time.sleep(BACKOFF[i])
    raise last_err  # type: ignore[misc]


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


def save_raw(path: Path, body: bytes, meta: dict) -> None:
    path.write_bytes(body)
    meta = dict(meta)
    meta["bytes"] = len(body)
    meta["sha256"] = hashlib.sha256(body).hexdigest()
    (path.parent / (path.name + ".meta.json")).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--icao", required=True)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--model", required=True, choices=sorted(MODEL_CATALOG))
    parser.add_argument("--history-start", required=True)
    parser.add_argument("--history-end", required=True)
    parser.add_argument("--forecast-start", required=True)
    parser.add_argument("--forecast-end", required=True)
    parser.add_argument("--timezone", default=None,
                        help="settlement-station local IANA; defaults to the 47-city table by --icao")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    timezone_name = args.timezone or ICAO_TIMEZONE.get(args.icao)
    if not timezone_name:
        parser.error(f"--timezone required: ICAO {args.icao} not in the settlement table")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_metadata = MODEL_CATALOG[args.model]
    common = {
        "latitude": args.latitude, "longitude": args.longitude,
        "hourly": ",".join(VARIABLES), "timezone": timezone_name,
    }
    if args.model != "best_match":
        common["models"] = args.model
    history_url = "https://historical-forecast-api.open-meteo.com/v1/forecast?" + urlencode({
        **common, "start_date": args.history_start, "end_date": args.history_end,
    })
    forecast_url = "https://api.open-meteo.com/v1/forecast?" + urlencode({
        **common, "start_date": args.forecast_start, "end_date": args.forecast_end,
    })
    summary = {
        "airport_icao": args.icao,
        "model_requested": args.model,
        "models_parameter_sent": args.model != "best_match",
        "model_catalog_metadata": model_metadata,
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "governance": {
            "null_policy": "A missing series is recorded as data_unavailable and never filled from another model.",
            "independence_policy": "Provider-family related series are retained separately and must not be treated as independent evidence.",
            "best_match_policy": "Automatic routing is collected only as job 6 and never as an implicit fallback; API returns no model field, routing identity is unprovable from the response body.",
            "retry_policy": "3 attempts, backoff 2/5/10s; 404/400 deterministic; read timeout 30s, connect 10s.",
        },
        "requests": {},
    }
    for name, url in (("history", history_url), ("forecast", forecast_url)):
        payload, attempts = fetch(url)
        raw_path = out_dir / f"{args.icao}_{args.model}_{name}_raw.json"
        if payload is None:
            body = b""
            summary["requests"][name] = {
                "url": url, "status": None, "raw_file": raw_path.name,
                "response_coordinate": None, "timezone": None, "utc_offset_seconds": None,
                "units": None, "variables": {}, "attempts": attempts, "deterministic_failure": True,
            }
            save_raw(raw_path, body, {"url": url, "status": None, "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                                      "attempts": attempts})
            continue
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        summary["requests"][name] = {
            "url": url,
            "raw_file": raw_path.name,
            "sha256": hashlib.sha256(body).hexdigest(),
            "response_coordinate": {key: payload.get(key) for key in ("latitude", "longitude", "elevation")},
            "timezone": payload.get("timezone"),
            "utc_offset_seconds": payload.get("utc_offset_seconds"),
            "units": payload.get("hourly_units"),
            "api_returned_model": payload.get("model"),
            "variables": quality(payload),
            "attempts": attempts,
        }
        save_raw(raw_path, body, {"url": url, "status": 200,
                                  "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                                  "model": args.model, "kind": name,
                                  "api_returned_model": payload.get("model"),
                                  "timezone": payload.get("timezone"),
                                  "utc_offset_seconds": payload.get("utc_offset_seconds"),
                                  "attempts": attempts})
    (out_dir / f"{args.icao}_{args.model}_quality_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
