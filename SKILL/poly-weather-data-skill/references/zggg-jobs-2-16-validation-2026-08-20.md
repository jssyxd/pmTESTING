# Open-Meteo 作业2–16逐项验证矩阵

- 机场：`ZGGG`；坐标：23.3933, 113.3083`
- 历史窗口：2026-08-18 至 2026-08-20（预期72行）；未来窗口：24小时。
- 采集时间（UTC）：2026-08-20T20:36:51.279962+00:00
- 判定规则：历史和未来均需HTTP 200、行数分别为72/24且全部目标变量非空，否则为`data_unavailable`，不做填补。

| 作业 | 模型ID | 类型 | 历史（HTTP/行数/判定） | 未来（HTTP/行数/判定） | 备注 |
|---:|---|---|---|---|---|
| 2 | `ecmwf_ifs` | deterministic | 200/72/pass | 200/24/pass | ECMWF_IFS |
| 3 | `ecmwf_aifs025_single` | deterministic_ai | 200/72/pass | 200/24/pass | ECMWF_AIFS |
| 4 | `gfs_seamless` | seamless | 200/72/pass | 200/24/pass | NOAA_GFS |
| 5 | `icon_seamless` | seamless | 200/72/pass | 200/24/pass | DWD_ICON |
| 6 | `best_match` | automatic_non_fixed | 200/72/pass | 200/24/pass | 省略models，自动路由 |
| 7 | `dwd_icon_global` | deterministic | 200/72/pass | 200/24/pass | DWD_ICON |
| 8 | `ncep_gfs_global` | deterministic | 200/72/pass | 200/24/pass | NOAA_GFS |
| 9 | `ecmwf_ifs025` | deterministic | 200/72/pass | 200/24/pass | ECMWF_IFS |
| 10 | `arpege_world` | deterministic | 200/72/pass | 200/24/pass | METEO_FRANCE_ARPEGE |
| 11 | `ukmo_global_deterministic_10km` | deterministic | 200/72/pass | 200/24/pass | UKMO |
| 12 | `jma_gsm` | deterministic | 200/72/pass | 200/24/pass | JMA |
| 13 | `gem_global` | deterministic | 200/72/pass | 200/24/pass | ECCC_GEM |
| 14 | `cma_grapes_global` | deterministic | 200/72/pass | 200/24/pass | CMA_GRAPES |
| 15 | `ncep_aigfs025` | deterministic_ai | 200/72/pass | 200/24/pass | NOAA_AIGFS |
| 16 | `ncep_hgefs025_ensemble_mean` | ensemble_mean | 200/72/pass | 200/24/pass | 集合平均；不可视为单一确定性模型 |

**结果：15/15项通过；其余项必须保留原始响应并标注`data_unavailable`。**
