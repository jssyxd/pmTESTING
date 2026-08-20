# Source priority and fallback policy

Use this policy only after reading the skill core workflow.

| Role | Primary route | Fallback order | Output limitation |
|---|---|---|---|
| Historical answer | WU history daily pages | none | The data table can contain temperature and qualitative condition but no defensible cloud-cover percentage. |
| Historical check | AWC METAR JSON | IEM CN__ASOS, then archival webpage | Preserve raw METAR. Treat all METAR display/redistribution paths as potentially related. |
| TAF extrema | AWC TAF JSON | Ogimet, Aaltronav | Parse TX/TN only. |
| Model history | Open-Meteo Historical Forecast API | explicit second model | No default model routing for a backtest. |
| Future model | Open-Meteo Forecast API | explicit second model | Record response grid point and source-run freshness. |

Use at least three retrieval modes across the complete workflow: public API (Open-Meteo/AWC/IEM), public webpage (WU/Ogimet/Aaltronav), and stored raw response. A retrieval mode is a resilience channel, not evidence of independent weather observations.

When a route fails, log the endpoint, request time, status/error, expected fields and fallback selected. Stop after the prescribed fallbacks and emit `data_unavailable`.
