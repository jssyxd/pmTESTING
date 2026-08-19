# 2026-08-18 Structured Report — ZSPD 2m Temperature Bias Preparation

## Data Lineage Declaration (Mandatory First)
- observation_source: Weather Underground ZSPD half-hourly (UTC+8), treated with METAR as gold standard. WU & METAR homologous risk noted; no double weighting.
- model_sources: ECMWF IFS HRES (Open-Meteo ecmwf_ifs), ECMWF AIFS Single (Open-Meteo ecmwf_aifs025_single)
- api_layer: Open-Meteo + Ogimet TAF archive + WU history
- upstream_dependency: Shared Grok conversation https://grok.com/share/c2hhcmQtMw_ab8a7b39-69b1-4072-b972-392cdb2f3a63 (cutoff ~2026-08-18 18:35 UTC+8)
- qc_notes: WU integer °C; models 0.1 °C. TAF only TX/TN discrete points. Past ~72 h window used. No imputation.

## Error Definition (Permanent)
Error = Observation - Model  
Positive Error = Model too cold; Negative Error = Model too warm.

## Hour-Layer Rules Applied
- mode=max (highest temperature): only 12:00–16:00 UTC+8 errors from past 72 h
- mode=min (lowest temperature): only 00:00–05:00 UTC+8 errors from past 72 h
- Bias estimation method: EWMA α=0.35 or recent valid sample rolling mean

## Available Data Summary (from shared conversation)
### WU Observations (selected)
2026-08-18 12:00–15:00 UTC+8: 30–31 °C
2026-08-17 12:00–16:00: ~30–31 °C
Nighttime mins around 25–27 °C

### TAF TX/TN (historical)
Multiple TX 30–32 °C around 14:00 UTC+8, TN 26–27 °C around 05:00 UTC+8

### IFS HRES hourly (sample)
2026-08-18 12–16 UTC+8: ~28.9 to 28.9 °C range in available points
Earlier days available but pairing for bias requires exact concurrent obs.

### AIFS hourly
Similar coverage; lead-time notes provided in original.

## Basis for Structured Extraction
All numbers taken verbatim from the shared conversation tables. No values invented. Missing concurrent pairs for full 72 h hour-layer statistics explicitly noted.

## Warnings
- Data cutoff before current prediction day 2026-08-19
- Insufficient paired samples inside strict hour layers for robust EWMA at time of original pull