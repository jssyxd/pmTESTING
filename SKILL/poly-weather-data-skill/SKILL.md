---
name: poly-weather-data-skill
description: Collect, validate, align, and govern airport weather observations and numerical forecasts for weather-market analysis. Use when retrieving 72-hour WU/METAR history, TAF extrema, Open-Meteo model history or forecasts, cloud and precipitation impacts, multi-source fallbacks, or audit-ready UTC+8 weather tables.
---

# Poly Weather Data Skill

Use this skill for airport weather-market data collection. Produce **raw responses**, a canonical UTC+8 long table, an audit summary, and an explicit `data_unavailable` state for every missing field. Never synthesize hourly values from daily summaries.

## Required rules

State data lineage before analysis: `观测源 = ...；模型源 = ...；API/网页层 = ...；上下游依赖 = ...`.

Use the fixed convention: `Error = Observation - Model` (positive means the model is too cold). Keep WU, AWC, IEM, and other display/processing paths as cross-checks; do not claim they are statistically independent observations. Store raw payloads before transforming data. Keep UTC internally and a UTC+8 display field in every output row.

Do not fill nulls from another model, a nearby hour, or a historical mean. If a requested model returns all-null arrays, record its requested model ID, response grid coordinate, HTTP outcome, and `data_unavailable`.

## Source order

Read `references/source-priority.md` before collection. Use `references/data-schema.md` before writing outputs. Treat the source roles as follows.

| Data requirement | Primary | First fallback | Second fallback | Rule |
|---|---|---|---|---|
| Answer 1: historical temperature and qualitative weather | WU date page | Record unavailable | — | Use the historical table only; a displayed dash is missing, not zero. |
| Answer 2: historical METAR temperature and cloud layers | AWC API | IEM `CN__ASOS` | Aaltronav/METAR-TAF webpage | Preserve raw METAR. Cloud groups are categorical, not percent cloud cover. |
| Historical model forecast | Open-Meteo Historical Forecast API, explicit model | Another explicit model request | Mark unavailable | Do not use `best_match` for backtests. |
| Future 24-hour model forecast | Open-Meteo Forecast API, explicit model | Another explicit model request | Mark unavailable | Preserve `models`, grid coordinates, timezone and fetch time. |
| Job 0: WU future hourly forecast | WU hourly page only when an actual hourly table is visible | Mark unavailable | — | A day-level WU summary may be a qualitative cross-check but cannot become a generated hourly series. |
| Job 1: TAF | AWC TAF API | Ogimet current/historical TAF page | Aaltronav TAF archive | Extract only `TX`/`TN` extrema and valid times; never infer hourly temperatures. |

## Workflow

1. Define airport ICAO, station coordinates, requested 72-hour historical window, future 24-hour window, and `timezone=Asia/Shanghai`.
2. Call the bundled `scripts/fetch_openmeteo_bundle.py` separately for each explicit model. Request `temperature_2m,precipitation,rain,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,weather_code`. Save the raw JSON untouched.
3. Retrieve AWC METAR with `ids=<ICAO>&format=json&hours=72&taf=false`; retrieve current TAF with `ids=<ICAO>&format=json`. Retain the full raw text.
4. Retrieve WU daily pages using `/history/daily/<country>/<city>/<ICAO>/date/YYYY-MM-DD`. Save the page text; select the nearest report to each local hour. Store condition text separately from numeric cloud cover.
5. Use IEM only as a METAR fallback/cross-check. Its non-US precipitation field is not usable for rainfall analysis; preserve it raw and label rainfall unavailable.
6. Validate every variable: expected hour count, non-null coverage, units, returned grid coordinate, time continuity, and raw-response checksum. Refuse analysis when mandatory fields are unavailable.
7. Align observations and model rows by valid UTC hour, then calculate `Error = Observation - Model`. Keep a source-pair agreement table; never merge sources into an invented composite observation.
8. Emit raw data, canonical long tables, quality summary, `raw_forecasts`, `bias_estimates`, `corrected_forecast`, `f1`, `f2`, `weights`, and `polymarket_value_score`. Leave non-applicable analytic fields null instead of manufacturing values.

## Open-Meteo requirements

Read `references/open-meteo-model-catalog.md` before choosing a model. Use jobs 2–16 as a controlled **model catalog**, not as independent observations. Pass an explicit `models` value except for job 6 (`best_match`), which intentionally omits `models` and must be labeled automatic/non-fixed. Save the request URL, returned latitude, longitude, elevation, units, timezone, `utc_offset_seconds`, requested model ID, catalog metadata, source endpoint, and fetch timestamp. The bundled script handles only the Open-Meteo model part; it does not replace observation collection.

Never use one model's value to fill another model's null field. Do not treat `gfs_seamless` and `ncep_gfs_global`, or `icon_seamless` and `dwd_icon_global`, as independent evidence: each pair belongs to the same provider/model family. Label `ncep_hgefs025_ensemble_mean` as an **ensemble mean**, never as a deterministic single model. Do not claim a fixed upstream, fixed spatial resolution, or fixed model identity for `best_match`.

Example:

```bash
python scripts/fetch_openmeteo_bundle.py \
  --icao ZGGG --latitude 23.3933 --longitude 113.3083 \
  --model ecmwf_ifs025 --history-start 2026-08-18 --history-end 2026-08-20 \
  --out-dir ./out/ZGGG
```

For an all-null response, create a quality record with `status=data_unavailable`; do not silently retry with `best_match`. `best_match` may only be collected as its own job 6 series and never as an implicit replacement.

## HTML audit view

Copy `templates/weather_data_dashboard.html` and populate it only from saved quality summaries and long tables. The page must distinguish `available`, `partial`, and `data_unavailable`; display source lineage and source-specific limitations. The HTML is an audit artifact, not a replacement for raw files.
