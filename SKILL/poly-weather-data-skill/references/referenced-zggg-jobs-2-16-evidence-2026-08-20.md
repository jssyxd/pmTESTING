# 引用任务：ZGGG 作业2–16验证证据汇总

本文件由引用任务的两份原始覆盖报告汇总：`referenced_zggg_primary_coverage_report.json`（创建于2026-08-20T18:54:24Z）覆盖作业2–6；`referenced_workbook_model_coverage_report.json`（锚点2026-08-21T02:00+08:00）覆盖作业2、3及作业7–16。两份报告的历史窗口均为72行、未来窗口均为24行，目标变量为温度、降水和云量。

| 作业 | 模型ID | 引用报告 | 历史72小时 | 未来24小时 | 温度/降水/云量空值 |
|---:|---|---|---|---|---|
| 2 | `ecmwf_ifs` | primary + workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 3 | `ecmwf_aifs025_single` | primary + workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 4 | `gfs_seamless` | primary | 72/72 | 24/24 | 0 / 0 / 0 |
| 5 | `icon_seamless` | primary | 72/72 | 24/24 | 0 / 0 / 0 |
| 6 | omit `models` (`best_match`) | primary | 72/72 | 24/24 | 0 / 0 / 0 |
| 7 | `dwd_icon_global` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 8 | `ncep_gfs_global` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 9 | `ecmwf_ifs025` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 10 | `arpege_world` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 11 | `ukmo_global_deterministic_10km` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 12 | `jma_gsm` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 13 | `gem_global` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 14 | `cma_grapes_global` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 15 | `ncep_aigfs025` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |
| 16 | `ncep_hgefs025_ensemble_mean` | workbook | 72/72 | 24/24 | 0 / 0 / 0 |

## 解释约束

引用证据只证明指定日期、指定位置、指定端点的可用性；不能保证后续日期、所有变量或所有机场都可用。每次执行仍必须保存实时请求URL、HTTP状态、API返回网格点、原始文件和新鲜度。`best_match`是自动选择；作业4与作业8同属NOAA GFS家族，作业5与作业7同属DWD ICON家族；作业16是集合平均。它们不得以独立观测的方式叠加权重，亦不得互相填补空值。
