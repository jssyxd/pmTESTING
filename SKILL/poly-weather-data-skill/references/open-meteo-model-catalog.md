# Open-Meteo controlled model catalog: jobs 2–16

Use this catalog with the task's fixed variables: `temperature_2m`, `precipitation`, `rain`, `cloud_cover`, `cloud_cover_low`, `cloud_cover_mid`, `cloud_cover_high`, and `weather_code`. All stated availability refers to the referenced ZGGG validation window: historical 72 hours and future 24 hours, with target variables non-null unless otherwise noted. Re-run the quality gate every execution; this catalog is not a guarantee for later runs.

| Job | Display name | `models` request | Type / governance | ZGGG referenced validation |
|---:|---|---|---|---|
| 2 | ECMWF IFS HRES | `ecmwf_ifs` | Deterministic; save API response grid point. | 72/72 historical, 24/24 future. |
| 3 | ECMWF AIFS 0.25° Single | `ecmwf_aifs025_single` | Deterministic AI model; do not infer a single fixed run from the request alone. | 72/72, 24/24. |
| 4 | NOAA GFS | `gfs_seamless` | Seamless composite; same NOAA family as job 8, not independent. | 72/72, 24/24. |
| 5 | DWD ICON | `icon_seamless` | Seamless composite; same DWD family as job 7, not independent. | 72/72, 24/24. |
| 6 | best_match | omit `models` | Automatic routing; non-fixed upstream/model identity. | 72/72, 24/24. |
| 7 | DWD ICON Global | `dwd_icon_global` | Deterministic global; related to job 5. | 72/72, 24/24. |
| 8 | NOAA GFS Global | `ncep_gfs_global` | Deterministic global; related to job 4. | 72/72, 24/24. |
| 9 | ECMWF IFS 0.25° | `ecmwf_ifs025` | Deterministic; do not fill it with job 2. | 72/72, 24/24. |
| 10 | Météo-France ARPEGE World | `arpege_world` | Deterministic global. | 72/72, 24/24. |
| 11 | UKMO Global | `ukmo_global_deterministic_10km` | Deterministic global. | 72/72, 24/24. |
| 12 | JMA GSM | `jma_gsm` | Deterministic global. | 72/72, 24/24. |
| 13 | Canadian GEM Global | `gem_global` | Deterministic global. | 72/72, 24/24. |
| 14 | CMA GFS GRAPES | `cma_grapes_global` | Deterministic global. | 72/72, 24/24. |
| 15 | NOAA AIGFS | `ncep_aigfs025` | Deterministic AI model. | 72/72, 24/24. |
| 16 | NOAA HGEFS ensemble mean | `ncep_hgefs025_ensemble_mean` | **Ensemble mean; not a deterministic model.** | 72/72, 24/24. |

## Selection rules

Do not use all available models as equal-weight independent votes. First group by `provider_family`: `NOAA_GFS` for jobs 4/8, `DWD_ICON` for jobs 5/7, and unique families for the other rows. Preserve each series separately in `raw_forecasts`; determine model weights only after walk-forward historical validation. A model's resolution or nominal update interval may be descriptive metadata, but the actual returned grid coordinate and request timestamp are the evidence to retain.

For each job, issue one historical request and one forecast request. Require all requested arrays to have non-null coverage for the target window. If an array is empty or all null, retain the response and set that model-window status to `data_unavailable`; do not fall back to a sibling, seamless, or automatic series.
