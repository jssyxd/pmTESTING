---
name: poly-weather-data-skill
description: Collect, validate, align, and govern airport weather observations and numerical forecasts for weather-market analysis. Use when retrieving 72-hour WU/METAR history, TAF extrema, Open-Meteo model history or forecasts, cloud and precipitation impacts, multi-source fallbacks, or audit-ready weather tables keyed to each settlement station's local IANA timezone.
---

# Poly Weather Data Skill

Use this skill for airport weather-market data collection. Produce **raw responses first**, a canonical station-local long table, an audit summary, and an explicit `data_unavailable` state for every missing field. Never synthesize hourly values from daily summaries.

**Anti-hallucination core:** every value in a delivered document MUST trace to a saved raw file in the same city evidence directory; never draft a data block before the raw response is on disk; never hand-write meta files, checksums, audit JSON, or event URLs — scripts write them; "fetch succeeded" or "checksum passed" is never itself output evidence. A prior review rejected a delivery for: 752 referenced raw paths with zero files on disk, best_match tables byte-identical to another model, 188 placeholder URLs, and a job-0 block claiming success with zero output rows. This skill is structured to make those four failure modes impossible.

## Required rules

State data lineage before analysis: `观测源 = ...；模型源 = ...；API/网页层 = ...；上下游依赖 = ...`.

Use the fixed convention: `Error = Observation - Model` (positive means the model is too cold). Keep WU, AWC, IEM, and other display/processing paths as cross-checks; do not claim they are statistically independent observations. Store raw payloads before transforming data. Keep UTC internally and a station-local display field (IANA per settlement station, from the city table) in every output row — do NOT hardcode UTC+8.

**Raw sidecar meta contract (all sources, WU/AWC/Ogimet/Open-Meteo/Polymarket):** every saved raw response MUST have a sidecar meta file (`<name>.meta.json`) with exactly: `url` (resolved, no placeholders), `status`, `fetched_at_utc` (the request completion moment, matching the run log ts — never the anchor), `bytes`, `sha256` (computed at save time). Additional optional fields: `date`, `unit_view`, `kind`, `model`, `api_returned_model`, `utc_offset_seconds`, `attempts` (per-retry record). The fetch script writes the meta; the document stage MUST NOT write or patch meta — a missing field means that block's values are unwritable and the block is re-fetched. The anchor time is stored separately as `anchor_utc`; never conflate it with `fetched_at_utc`.

Do not fill nulls from another model, a nearby hour, or a historical mean. If a requested model returns all-null arrays, record its requested model ID, response grid coordinate, HTTP outcome, and `data_unavailable`.

**best_match identity rule:** Open-Meteo responses do not include a model identifier (`api_returned_model=null`); best_match routing identity cannot be proven from the response body. Job 6 documents MUST state this and record the returned grid point; when the returned grid and values coincide with a sibling model (e.g. `ecmwf_ifs` at the same grid — real Open-Meteo routing, observed for ZSPD), state the coincidence explicitly and keep the byte-different raw files as the only identity evidence. Numerical equality is NOT copying evidence; byte-for-byte equality of the raw files would be. Never claim best_match "is" a fixed model.

**WU unit views:** fetch metric and english views per date; compute per-(date) sha256 pair at fetch time and write `raw/wu_daily_unit_compare.json` (fields: date, metric_sha256, english_sha256, bytes_equal, note). Document statements about view identity must cite that file. As of 2026-08-21, WU serves byte-identical pages for `cm_units=metric|english`, cookies included (187/188 slices identical) — native ℉ is unobtainable from the public page; record `bytes_equal=true` as the evidence and write ℉=null. Never claim a native ℉ view was obtained without a raw file containing it.

## Source order

Read `references/source-priority.md` before collection. Use `references/data-schema.md` before writing outputs. Treat the source roles as follows.

| Data requirement | Primary | First fallback | Second fallback | Rule |
|---|---|---|---|---|
| Answer 1: historical temperature and qualitative weather | WU date page | Record unavailable | — | Use the historical table only; a displayed dash is missing, not zero. Both unit views fetched; identity evidenced via `wu_daily_unit_compare.json`. |
| Answer 2: historical METAR temperature and cloud layers | AWC API | IEM `CN__ASOS` | Aaltronav/METAR-TAF webpage | Preserve raw METAR. Cloud groups are categorical, not percent cloud cover. |
| Historical model forecast | Open-Meteo Historical Forecast API, explicit model | Another explicit model request | Mark unavailable | Do not use `best_match` for backtests. |
| Future 24-hour model forecast | Open-Meteo Forecast API, explicit model | Another explicit model request | Mark unavailable | Preserve `models`, grid coordinates, timezone and fetch time. |
| Job 0: WU future hourly forecast | WU hourly page only when an actual hourly table is visible | Mark unavailable | — | Structural parse (hour container, distinct hour rows, date consistency) is required to claim success; "page fetched" is not evidence. A day-level WU summary may be a qualitative cross-check but cannot become a generated hourly series. |
| Job 1: TAF | AWC TAF API | Ogimet current/historical TAF page | Aaltronav TAF archive | Extract only `TX`/`TN` extrema and valid times; never infer hourly temperatures. Ogimet historical archive known 404 since 2026-08-21 (273-byte error page, 94/94): record as a dated known limitation, send one probe per round, restore full fetch the round the probe passes. |

## Workflow

1. Define airport ICAO, station coordinates, requested 72-hour historical window, future 24-hour window, and `timezone=<settlement station's local IANA>` (from the city table — never a fixed UTC+8). Express historical/forecast windows as **station-local calendar dates** (history = local day of anchor−72h through local day of anchor; forecast = local day of anchor through local day of anchor+24h, full start/end days included), derived from the anchor.
2. Call the bundled `scripts/fetch_openmeteo_bundle.py` separately for each explicit model. Request `temperature_2m,precipitation,rain,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,weather_code`. Save the raw JSON untouched.
3. Retrieve AWC METAR with `ids=<ICAO>&format=json&hours=72&taf=false`; retrieve current TAF with `ids=<ICAO>&format=json`. Retain the full raw text.
4. Retrieve WU daily pages using `/history/daily/<country>/<city>/<ICAO>/date/YYYY-MM-DD`. Save the page text; select the nearest report to each local hour. Store condition text separately from numeric cloud cover. Save both unit views and write `wu_daily_unit_compare.json`.
5. Use IEM only as a METAR fallback/cross-check. Its non-US precipitation field is not usable for rainfall analysis; preserve it raw and label rainfall unavailable.
6. Validate every variable: expected hour count, non-null coverage, units, returned grid coordinate, time continuity, and raw-response checksum. Refuse analysis when mandatory fields are unavailable.
7. Align observations and model rows by valid UTC hour, then calculate `Error = Observation - Model`. Keep a source-pair agreement table; never merge sources into an invented composite observation.
8. Emit raw data, canonical long tables, quality summary, `raw_forecasts`, `bias_estimates`, `corrected_forecast`, `f1`, `f2`, `weights`, and `polymarket_value_score`. Leave non-applicable analytic fields null instead of manufacturing values.
9. **Delivery gate (before finalizing any city document):** (a) every `raw_file` referenced by the document exists with a complete meta (url/status/fetched_at_utc/bytes/sha256); (b) no literal placeholders remain (`{country}`, `{city}`, `{ICAO}`, `ids=ICAO`, `icao=ICAO`, `day=DD`, `month=MM`, `year=YYYY`, literal `YYYY-MM-DD` template style); (c) model-page rows are compared against the raw arrays in full, WU pages with a fixed-seed sample (JSON sources field-compared, HTML sources compared post-parse); result in `doc_traceability_audit.json`. Run `scripts/verify_doc_lineage.py`; the agent only runs the script and never hand-writes audit artifacts. Regenerate any page that fails; never deliver a page whose numbers cannot be traced to a saved raw file.

## Open-Meteo requirements

Read `references/open-meteo-model-catalog.md` before choosing a model. Use jobs 2–16 as a controlled **model catalog**, not as independent observations. Pass an explicit `models` value except for job 6 (`best_match`), which intentionally omits `models` and must be labeled automatic/non-fixed. Save the request URL, returned latitude, longitude, elevation, units, timezone, `utc_offset_seconds`, requested model ID, catalog metadata, source endpoint, and fetch timestamp. The bundled script handles only the Open-Meteo model part; it does not replace observation collection.

Never use one model's value to fill another model's null field. Do not treat `gfs_seamless` and `ncep_gfs_global`, or `icon_seamless` and `dwd_icon_global`, as independent evidence: each pair belongs to the same provider/model family. Label `ncep_hgefs025_ensemble_mean` as an **ensemble mean**, never as a deterministic single model. Do not claim a fixed upstream, fixed spatial resolution, or fixed model identity for `best_match`.

**Retry and concurrency policy (applies to all network requests in every script):**
- Retry SSL/connection timeouts, HTTP 429, and 5xx up to 3 times with exponential backoff (2s/5s/10s, optional jitter). HTTP 404/400 are deterministic failures — do not retry; record as a known limitation.
- Per-attempt timeouts: connect/handshake 10–15s (fail fast — a 90s stall stalls the whole city); read timeout per source: WU 60s, Open-Meteo/AWC 30s.
- Open-Meteo concurrency ≤ 3 concurrent requests; on 429 back off and reduce concurrency, never increase it.
- Log every retry attempt (attempt number, time, status, Retry-After if present) and persist failed attempts (`<name>_attempt<N>_error.*` or meta `attempts` list); the final raw file is the last successful response.
- Run completion events keep the established vocabulary (`PULL_COMPLETE` etc.) and add a `fetch_gaps` field aggregating failures by block plus a status of `complete|complete_with_gaps`; never declare gap-free completion when gaps exist.

Example:

```bash
python scripts/fetch_openmeteo_bundle.py \
  --icao ZGGG --latitude 23.3933 --longitude 113.3083 \
  --model ecmwf_ifs025 --history-start 2026-08-18 --history-end 2026-08-20 \
  --forecast-start 2026-08-20 --forecast-end 2026-08-21 \
  --timezone Asia/Shanghai \
  --out-dir ./out/ZGGG
```

For an all-null response, create a quality record with `status=data_unavailable`; do not silently retry with `best_match`. `best_match` may only be collected as its own job 6 series and never as an implicit replacement.

To independently audit the entire catalog after a model or endpoint change, run `scripts/validate_openmeteo_catalog.py` and then `scripts/summarize_catalog_validation.py`. Save the JSON payload and Markdown matrix with the date, airport, window and request timestamp. The matrix is a point-in-time execution record; repeat it rather than assuming a past pass applies to a new date.

## Coverage audit records (per city)

Regional-model coverage must be judged per city from this round's actual requests (or explicit "not requested + reason"), never copied from another city's conclusion or inferred from coordinate lists. As of the 2026-08-20/21 run, `jma_gsm`, `cma_grapes_global`, and `ncep_hgefs025_ensemble_mean` returned complete non-null data at KBKF/NZWN — the old "non-China coordinates are null" conclusion is void. `ecmwf_ifs04` and `bom_access_global` are field-unavailable (all-null) per the dated ZGGG validation record (`references/zggg-jobs-2-16-validation-2026-08-20.md`); per-city rows may cite that dated record when not re-requested this round, and MUST NOT hardcode HTTP statuses or row counts.

## HTML audit view

Copy `templates/weather_data_dashboard.html` and populate it only from saved quality summaries and long tables. The page must distinguish `available`, `partial`, and `data_unavailable`; display source lineage and source-specific limitations. The HTML is an audit artifact, not a replacement for raw files.
