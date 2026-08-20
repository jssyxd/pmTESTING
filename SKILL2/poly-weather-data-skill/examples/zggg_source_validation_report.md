# ZGGG 多源天气数据验证与抓取方案

**样本对象：**广州白云国际机场（ZGGG），输入坐标 **23.3933°N, 113.3083°E**。本报告记录一次以 2026-08-21 02:00（UTC+8）为锚点的验证。历史窗口为 2026-08-18 02:00 至 2026-08-21 02:00（结束时刻不含），未来窗口为 2026-08-21 02:00 后的 24 个整点至 2026-08-22 02:00（含结束时刻）。所有样本时间均以 UTC+8 对齐，原始证据和规范化 CSV 位于同目录 `zggg_validation/`。

> **结论。** 本次验证已成功取得 Open-Meteo 五个指定模型各 **72 条历史预报小时 + 24 条未来预报小时**，字段含 2 米温度、总降水、雨量以及总/低/中/高云量；AWC METAR 成功取得 **143 条**实际观测间隔报文。当前 TAF 成功取得并解析 TX/TN。Weather Underground 的历史日表可在浏览器获得实际观测时间、温度、降水及天气状态，但本次未将三个日页的完整数据导入样本；未来 WU 分时页没有得到可核验的完整 24 小时表。因此，本技能明确将 WU 未取到的字段写为 `null`，而不以任何其他来源补齐。

## 已验证结果

| 区块 | 一级来源 | 本次状态 | 可用数据 | 严格限制 |
|---|---|---:|---|---|
| 作业 0 | Weather Underground 小时预报网页 | 未完成 | 无完整、日期一致的 24 小时表 | 不用日摘要伪造小时值；温度、降水、云量保持 `null`。 |
| 作业 1 | AWC 当前 TAF API | 成功 | 原始 TAF、TX/TN | 这是当前预报，不是过去 72 小时的 TAF 发布归档。 |
| 作业 2 | Open-Meteo `ecmwf_ifs` | 成功 | 72+24 小时、温度/降水/云量 | 数值模式，不是站点观测。 |
| 作业 3 | Open-Meteo `ecmwf_aifs025_single` | 成功 | 72+24 小时、温度/降水/云量 | 数值模式，不是站点观测。 |
| 作业 4 | Open-Meteo `gfs_seamless` | 成功 | 72+24 小时、温度/降水/云量 | 无缝/组合域；不要假定单一固定网格。 |
| 作业 5 | Open-Meteo `icon_seamless` | 成功 | 72+24 小时、温度/降水/云量 | 无缝/组合域；不要假定单一固定网格。 |
| 作业 6 | Open-Meteo 默认 `best_match` | 成功 | 72+24 小时、温度/降水/云量 | 自动选择，不是固定模型。 |
| 答案 1 | WU 历史日页 | 需渲染适配器 | 单日页的实际时刻、温度、降水、Condition 已核验 | 没有数值云量就输出 `null`；不能把 Condition 映射为云量百分比。 |
| 答案 2 | AWC METAR JSON | 成功 | 143 条实际观测时间、温度、云况、天气现象、原报文 | 数值降水字段缺失即 `null`；云况代码不换算为百分比。 |

## Open-Meteo 官方实现与数据血缘

Open-Meteo 的 Historical Forecast API 归档数值天气预报运行，而不是同化后的站点实况。官方文档将 `temperature_2m`、`precipitation`、`rain`、`cloud_cover` 和分层云量列为逐小时变量，并说明历史预报时间序列会拼接不同运行的开头数小时；若要获得一个固定运行的完整预报时效，应使用 Single Runs API。[1] 这意味着历史序列的血缘必须记录“Historical Forecast API 拼接运行”，而不是杜撰为单一固定起报时次。

官方仓库显示服务会整合多个国家气象服务的开放模式资料，并在 `Sources/App` 中分设 ECMWF、GFS、ICON、CMA、JMA 等处理目录。[2] `ForecastapiController.swift` 的路由进一步表明 `ecmwf_ifs` 映射到 ECMWF 域，而 `best_match`、`gfs_seamless`、`icon_seamless` 并非普通单域直映射。故技能把**每次 API 实际返回的经纬度、海拔、时区和请求 URL**作为证据，避免对分辨率、网格点或固定上游作超出响应证据的声明。

本样本中可见返回网格点确与输入点略有差异，例如 IFS 返回 23.37434°N、113.350845°E；AIFS 返回 23.5°N、113.25°E。此差异必须在作业页头保留，不能称为“机场站点温度”。

## 航空气象与网页来源评估

Clarmy 的资料指出 AWC 提供公开航空气象 API，并展示了 ZGGG METAR JSON 示例与 `hours` 回溯用法。[3] 实测中 `https://aviationweather.gov/api/data/metar?ids=ZGGG&format=json&taf=false&hours=72` 成功。其 JSON 内可包含温度、云层、天气现象和原始报文，但不应从 `-SHRA` 等文字倒推毫毫米降水。

TAF 与 METAR 是不同类别。当前 AWC 请求 `https://aviationweather.gov/api/data/taf?ids=ZGGG` 成功返回：

```text
TAF ZGGG 201503Z 2018/2124 09003MPS 8000 BKN040
TX34/2107Z TN27/2022Z TN28/2122Z TEMPO 2106/2109 TSRA SCT026CB BKN033
```

其中 `TX34/2107Z` 是 34°C、UTC 21 日 07:00（UTC+8 15:00）；`TN27/2022Z` 和 `TN28/2122Z` 必须原样逐项保留。带 `format=raw` 的 AWC TAF 请求被拒绝，带 `format=json&hours=72` 的一次请求返回 HTTP 504；因此它们是可审计的失败事实，而非用当前 TAF 冒充历史 TAF 的理由。

IEM 的 CN__ASOS 页面列出 ZGGG，给出可脚本化的 `asos.py` 请求模式，并说明其历史集基本未做质量控制；页面还指出非美国站点降水不可用。[4] 这使 IEM 成为历史 METAR 温度/原报文的有效兜底，却不适合作为 ZGGG 数值降水兜底。UCAR/EOL 100.013 包含按月分发的全球逐小时 METAR ASCII 文件、标记为 final，覆盖页面所列截止至 2026-05-31，故只适合较早期的最终质控归档，而非 2026-08 的近 72 小时。[5]

Ogimet 的 `metars.phtml.en` 表单支持 ICAO、UTC 起止时刻、HTML/TXT 和 TAF 类型选择，长 TAF 使用 `FT`；它可作为历史 TAF 的网页级二级路径。[6] 本次范围请求返回空白，因而没有把它记成成功样本。AALTROnav 提供 ICAO、日期范围及 METAR/TAF 表单，但需逐次验证访问与登录限制。[7] METAR-TAF.com 可展示 ZGGG 当前原报文和云况，但历史入口提示登录，故仅适合人工核验，不得假设可稳定免费批量抓取。[8]

## 鲁棒性策略

每次运行先保存请求和响应（成功、非 200、超时都保存）。Open-Meteo 采用显式模型逐一请求；某模型失败时只把该模型对应作业标为失败，绝不用另一模型补值。METAR 采用 AWC → IEM → 网页人工核验；TAF 采用 AWC 当前原文 → Ogimet 历史范围表单 → AALTROnav/人工归档；WU 采用渲染页表 → 静态表 → 另标注的模式辅助。所有路径均在 HTML 中标记为观测、模式或聚合网页三类血缘，防止把同源展示层误计为多个独立样本。

## 文件说明

| 文件 | 内容 |
|---|---|
| `zggg_weather_dashboard_sample.html` | 可直接打开的简洁 HTML 看板，包含完整五模型 96 小时表和最新 24 条 METAR。 |
| `zggg_validation/open_meteo_hourly.csv` | 五模型共 480 行的规范化小时数据。 |
| `zggg_validation/open_meteo_model_metadata.csv` | 每模型每数据段的返回网格点、时区和请求 URL。 |
| `zggg_validation/awc_metar_actual_observations.csv` | 143 条按实际观测时刻排序的 METAR。 |
| `zggg_validation/coverage_report.json` | 72/24 覆盖审计、当前 TAF 与 TX/TN 解析、WU 状态。 |
| `zggg_validation/manifest.json` 与 `request_status.csv` | 请求参数、URL、状态码与抓取证据。 |

## 参考文献

[1] [Open-Meteo Historical Forecast API](https://open-meteo.com/en/docs/historical-forecast-api)

[2] [Open-Meteo 官方仓库](https://github.com/open-meteo/open-meteo)

[3] [Clarmy：民航机场 METAR 数据源](https://www.clarmy.me/recommend-metar-data-sources/)

[4] [IEM：中国 ASOS/METAR 下载](https://mesonet.agron.iastate.edu/request/download.phtml?network=CN__ASOS)

[5] [NSF NCAR EOL 100.013：Global GTS Surface METAR](https://data.eol.ucar.edu/dataset/100.013)

[6] [Ogimet METAR/SPECI/TAF 历史查询](https://www.ogimet.com/metars.phtml.en)

[7] [AALTROnav METAR / TAF archive](https://aaltronav.eu/weather/metar/)

[8] [METAR-TAF.com ZGGG](https://metar-taf.com/zh/metar/ZGGG)
