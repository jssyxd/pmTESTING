# Minimum canonical fields

Store a raw file plus a long-table record for every observation or forecast value.

| Field | Requirement |
|---|---|
| `airport_icao` | ICAO airport code. |
| `source_role` | `answer_1_wu`, `answer_2_metar`, `taf`, `model_history`, or `model_forecast`. |
| `source_endpoint` | Full endpoint or webpage URL, excluding secrets; resolved (no placeholders). |
| `model_requested` | Explicit Open-Meteo model; null for observations. |
| `valid_time_utc` and `display_time_station_local` | Both required for time-aligned rows. `display_time_station_local` is the settlement station's local IANA timezone (from the city table); a `display_timezone` field records which IANA zone. Do not hardcode UTC+8. |
| `variable`, `value`, `unit` | One value per variable; preserve source unit. |
| `raw_file`, `raw_file_sha256`, `fetched_at_utc` | Required lineage. `raw_file_sha256` is the SHA-256 of the saved raw file bytes, computed at save time by the fetch script. |
| `status` | `available`, `partial`, or `data_unavailable`. |
| `reason` | Required when status is not `available`. Include the attempt time (UTC) and the evidence file path. |

For a model-vs-observation comparison, store both source row identifiers. Keep `error_c = observation_temperature_c - model_temperature_c`; do not calculate when either value is missing.

## Raw sidecar meta contract (every saved raw response)

The fetch script writes `<name>.meta.json` at save time. The document stage must never write or patch meta; a missing field marks that block's values unwritable and triggers a re-fetch.

| meta 字段 | 要求 |
|---|---|
| `url` | 实际请求/页面 URL（解析后，不含占位符） |
| `status` | HTTP 状态码；失败时保留错误体原文落盘 |
| `fetched_at_utc` | 请求完成时刻（ISO8601 UTC），必须与运行日志 ts 一致；**锚点时间单独存 `anchor_utc`，二者不得混写** |
| `bytes` | 落盘字节数 |
| `sha256` | 落盘文件 SHA-256（保存后立即计算） |
| `date` / `unit_view` / `kind` / `model` | 适用时：WU 日期与单位视图、history/forecast、请求模型 |
| `attempts` | 适用时：重试记录 `[{ts, status, error, bytes}]` |

## Time semantics

- `fetched_at_utc` = the moment the request completed (match the run log ts within ±1s). It is NOT the anchor (anchor = fetch moment floored to the hour, stored as `anchor_utc`). A 2026-08-21 audit found meta files stamped with the anchor (20:00Z) while requests actually completed ~55 minutes later — treat that as a record-discipline failure.
- Window boundaries: anchor −72h (history, exclusive) and anchor +24h (forecast, inclusive of the endpoint, exclusive of the anchor) in UTC; expressed in station-local calendar dates for Open-Meteo `start_date`/`end_date` parameters.
