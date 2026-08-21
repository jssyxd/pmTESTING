# Source priority and fallback policy

Use this policy only after reading the skill core workflow.

| Role | Primary route | Fallback order | Output limitation |
|---|---|---|---|
| Historical answer | WU history daily pages | none | The data table can contain temperature and qualitative condition but no defensible cloud-cover percentage. Native ℉ is unobtainable from the public page (unit params/cookies return byte-identical pages, verified 2026-08-21); evidence via `wu_daily_unit_compare.json`, ℉ column null. |
| Historical check | AWC METAR JSON | IEM CN__ASOS, then archival webpage | Preserve raw METAR. Treat all METAR display/redistribution paths as potentially related. |
| TAF extrema | AWC TAF JSON | Ogimet, Aaltronav | Parse TX/TN only. Ogimet historical archive is a known 404 since 2026-08-21 (273-byte Apache error page, 94/94 requests): record as a dated known limitation, send one probe per round, restore full fetch the round the probe passes; probe result (status, time) goes into the TAF page. |
| Model history | Open-Meteo Historical Forecast API | explicit second model | No default model routing for a backtest. |
| Future model | Open-Meteo Forecast API | explicit second model | Record response grid point and source-run freshness. |

Use at least three retrieval modes across the complete workflow: public API (Open-Meteo/AWC/IEM), public webpage (WU/Ogimet/Aaltronav), and stored raw response. A retrieval mode is a resilience channel, not evidence of independent weather observations.

When a route fails, log the endpoint, request time, status/error, expected fields and fallback selected. Stop after the prescribed fallbacks and emit `data_unavailable`.

## Failure, retry and evidence rules

- Every HTTP request: retry SSL/connection timeouts, 429, and 5xx up to 3 times with backoff 2s/5s/10s; 404/400 are deterministic — no retry, record as a known limitation. Connect/handshake timeout 10–15s; read timeout per source (WU 60s, Open-Meteo/AWC 30s). Open-Meteo concurrency ≤ 3.
- Every failure must be recorded with: reason, attempt time (UTC, request-completion moment), final status, and evidence location (raw meta file path; run-log line numbers are optional and only valid for that run). Never write "failed" or "no report" without a time and evidence.
- Failed attempts must leave a trace on disk (`<name>_attempt<N>_error.*` or meta `attempts`), so audits can count retries; the final raw file is the last successful response.
- Regional-model coverage / field-unavailability judgments must be per city from this round's actual requests (or explicit "not requested + reason"), never copied from another city or inferred from coordinate lists. Dated catalog validation records may be cited for models not re-requested this round (e.g. `ecmwf_ifs04`, `bom_access_global` — field-unavailable per `zggg-jobs-2-16-validation-2026-08-20.md`).
