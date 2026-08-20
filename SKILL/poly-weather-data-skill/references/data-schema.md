# Minimum canonical fields

Store a raw file plus a long-table record for every observation or forecast value.

| Field | Requirement |
|---|---|
| `airport_icao` | ICAO airport code. |
| `source_role` | `answer_1_wu`, `answer_2_metar`, `taf`, `model_history`, or `model_forecast`. |
| `source_endpoint` | Full endpoint or webpage URL, excluding secrets. |
| `model_requested` | Explicit Open-Meteo model; null for observations. |
| `valid_time_utc` and `display_time_utc8` | Both required for time-aligned rows. |
| `variable`, `value`, `unit` | One value per variable; preserve source unit. |
| `raw_file`, `request_hash`, `fetched_at_utc` | Required lineage. |
| `status` | `available`, `partial`, or `data_unavailable`. |
| `reason` | Required when status is not `available`. |

For a model-vs-observation comparison, store both source row identifiers. Keep `error_c = observation_temperature_c - model_temperature_c`; do not calculate when either value is missing.
