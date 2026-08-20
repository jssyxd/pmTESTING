# 工作簿全球模型审计与作业 9、作业 10 验证报告

**对象。** ZGGG / 23.3933°N、113.3083°E，时区 UTC+8。所有请求以 2026-08-21 02:00（UTC+8）为锚点；历史窗口为此前 72 个已结束整点，未来窗口为其后 24 个整点。报告源自 `工作簿1.xlsx` 的 68 行清单、Open-Meteo 官方文档/源码及本次保存的逐项 API 原始响应。

> **总结果。** 工作簿中明确全球覆盖的模型已按专属模型参数逐一实测；**12 个模型**同时取得完整、非空的 `72/72` 历史和 `24/24` 未来 2 米温度、降水与总云量。IFS 0.4° 与 BOM ACCESS-G 返回 HTTP 200 和完整时间列，但全部 96 个目标时次的温度、降水和云量均为 `null`，故不作为可用作业数据。欧洲、北美、日本、北欧、法国、英国/爱尔兰、加拿大及中欧区域模式依据工作簿覆盖范围被逐项标注为**地域排除**，没有发起对广州没有科学意义的伪请求。

## 作业 9 与作业 10

| 作业 | 模式与供应方 | 专属 API 模型参数 | 历史 / 未来覆盖 | 目标字段空值 | 血缘结论 |
|---|---|---|---:|---:|---|
| 作业 9 | CMA GFS GRAPES | `cma_grapes_global` | 72 / 24 | 0 / 0 / 0 | Open-Meteo 接入 CMA 全球数值模式；不是机场地面观测。 |
| 作业 10 | Météo-France ARPEGE World | `arpege_world` | 72 / 24 | 0 / 0 / 0 | Open-Meteo 接入 Météo-France 全球数值模式；不是机场地面观测。 |

作业 9 和作业 10 的完整 96 行逐小时表已嵌入 `zggg_weather_dashboard_sample.html`，并保存在 `workbook_model_validation/normalized/workbook_global_models_hourly.csv`。每行含当地 ISO 时间、历史/未来窗口、2 米温度（°C/°F）、总降水、雨量、总/低/中/高云量、返回网格点、原始请求 URL、抓取时间和原始文件路径。转换后的华氏温度只由 API 的摄氏温度换算；不存在插值、填充或跨模型替代。

## 工作簿的逐项处理

| 工作簿来源/模型 | ZGGG 处理 | 实测结论 | 证据或理由 |
|---|---|---|---|
| DWD ICON Global | 逐一实测 | 完整非空 72+24 | `dwd_icon_global`，历史/未来 HTTP 200。 |
| NOAA GFS Global | 逐一实测 | 完整非空 72+24 | `ncep_gfs_global`，历史/未来 HTTP 200。 |
| NOAA GFS Pressure Variables | 归入同一 GFS 全球来源 | 已有 GFS 温度、降水、云量；压力变量是同一模式的变量集 | 不是独立温度/云量模式，避免重复计数。 |
| NOAA AIGFS | 逐一实测 | 完整非空 72+24 | `ncep_aigfs025`，历史/未来 HTTP 200。 |
| NOAA HGEFS | 逐一实测 | 完整非空 72+24 | `ncep_hgefs025_ensemble_mean`，以 ensemble mean 取得。 |
| Météo-France ARPEGE World | 逐一实测 / 作业10 | 完整非空 72+24 | `arpege_world`。 |
| ECMWF IFS 0.4° | 逐一实测 | 时间列完整但字段不可用 | `ecmwf_ifs04`，96 个目标时次全 `null`。 |
| ECMWF IFS 0.25° | 逐一实测 | 完整非空 72+24 | `ecmwf_ifs025`。 |
| ECMWF AIFS 0.25° Single | 逐一实测 | 完整非空 72+24 | `ecmwf_aifs025_single`。 |
| ECMWF IFS HRES | 逐一实测 | 完整非空 72+24 | `ecmwf_ifs`。 |
| UKMO Global | 逐一实测 | 完整非空 72+24 | `ukmo_global_deterministic_10km`。 |
| JMA GSM | 逐一实测 | 完整非空 72+24 | `jma_gsm`。 |
| Canadian GEM Global | 逐一实测 | 完整非空 72+24 | `gem_global`。 |
| CMA GFS GRAPES | 逐一实测 / 作业9 | 完整非空 72+24 | `cma_grapes_global`。 |
| BOM ACCESS-G | 逐一实测 | 时间列完整但字段不可用 | `bom_access_global`，96 个目标时次全 `null`。 |
| ICON-EU、ICON-D2、HRRR、NAM、NBM | 地域排除 | 不适用于广州 | 欧洲或美国大陆覆盖。 |
| ARPEGE Europe、AROME France/HD | 地域排除 | 不适用于广州 | 欧洲或法国覆盖。 |
| UKMO UKV、JMA MSM、MET Nordic | 地域排除 | 不适用于广州 | 英国/爱尔兰、日本或北欧覆盖。 |
| GEM Regional、HRDPS Continental | 地域排除 | 不适用于广州 | 北美/加拿大覆盖。 |
| ARPAE ICON 2I、DMI/KNMI HARMONIE、ICON CH1/CH2 | 地域排除 | 不适用于广州 | 欧洲或中欧覆盖。 |

## 质量与鲁棒性规则

Open-Meteo 文档说明模型有不同的区域、分辨率和变量，并可能将原始时次插值到逐小时；因此本验证将 API 返回的时间序列、网格点、时区和单位一并保存，而不是仅接受工作簿中的标签。[1] 官方源码中的 `ForecastapiController.swift` 列举了 `arpege_world`、`cma_grapes_global`、`ncep_aigfs025`、`ncep_hgefs025_ensemble_mean`、`bom_access_global` 等公开模型参数，已用于本次请求。[2]

HTTP 成功不是数据成功。ACCESS-G 与 IFS 0.4° 的原始 JSON 有 ISO 时间数组和单位，但逐小时目标变量数组全部为 `null`；本报告据此将它们分为“字段不可用”，禁止用任意其他模式、METAR 或页面摘要填充。与之相对，12 个非空模型都需要继续保存自己的请求 URL 和原始 JSON；发生限流、4xx/5xx 或字段空缺时，应只降级该模型的作业，而不是跨源补值。

## 文件清单

| 文件 | 作用 |
|---|---|
| `workbook_model_inventory.md` | 68 行工作簿的全量清单、全球候选和地域排除分类。 |
| `workbook_source_research.md` | 官方文档与源码标识研究笔记。 |
| `workbook_model_validation/coverage_report.json` | 14 个全球候选的 HTTP、72/24 覆盖和空值计数。 |
| `workbook_model_validation/raw/` | 逐个模型、逐个历史/未来请求的原始 API 响应、URL、参数和响应头。 |
| `workbook_model_validation/normalized/workbook_global_models_hourly.csv` | 1,344 条规范化、无插值的模型小时记录。 |
| `zggg_weather_dashboard_sample.html` | 含作业 9、作业 10 的可直接打开数据看板。 |

## 参考文献

[1] [Open-Meteo Forecast API：Data Sources 与 Weather Models](https://open-meteo.com/en/docs)

[2] [Open-Meteo 官方源码仓库](https://github.com/open-meteo/open-meteo)
