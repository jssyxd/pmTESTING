---
name: poly-weather-data-skill
description: 拉取、核验并治理机场/坐标天气数据，生成可审计的 72 小时历史与未来 24 小时逐小时温度、降水、云量、METAR、TAF 和 Weather Underground 数据。用于需要多源兜底、时间对齐、严格数据血缘、禁止插值和 HTML 看板样本的天气数据作业。
---

# Poly Weather Data Skill

用此技能为一个 ICAO 机场和一组坐标构建可复现、可审计、**绝不插值**的天气数据包。默认时间区使用站点当地时间；中国站点使用 `Asia/Shanghai`（UTC+8）。

## 输入与固定变量

收集 `icao`、城市/站名、精确 `latitude`/`longitude`、时区、抓取时刻、历史窗口和未来窗口。默认将抓取锚定到整点：历史为锚点之前 72 个已结束整点，未来为锚点之后 24 个尚未来临的整点。保存原始抓取 UTC 时间。

Open-Meteo 的默认逐小时变量为 `temperature_2m`、`precipitation`、`rain`、`cloud_cover`、`cloud_cover_low`、`cloud_cover_mid`、`cloud_cover_high`。除非原始源明确提供，禁止补造其他字段。

## 不可违反的数据治理

每一份作业或答案开头都写入下面的**强制数据血缘声明**：

> 本轮使用的观测源是 [来源]，模型源是 [模型名或无]，API/网页层是 [服务]；是否存在上下游依赖：[是/否及说明]。此页不把同源或聚合展示层误视为独立观测样本。

保存原始响应到 `raw/`，并保存请求 URL、参数、HTTP 状态、响应头、抓取 UTC 时间、返回网格点、时区和单位到 `metadata/`。规范化记录必须回链原始文件和请求 URL。

缺失值写 `null`。严禁插值、外推、前后填充、用模型替代观测，或把天气文字转换成未提供的定量降水/云量。仅当原始温度单位明确为摄氏度时，输出 `℃` 一位小数，并按 `℉ = round(℃ × 9/5 + 32)` 输出整数华氏度。

不要把 Weather Underground、METAR-TAF.com 等聚合展示层与 AWC METAR 当成独立观测样本。不要把 TAF 当成观测，更不能把 TAF 的 TX/TN 展开为虚假的逐小时温度序列。

## 三层获取路径

前一条失败时，先保存失败证据再尝试下一条。不同路径来自同一上游时必须标记同源，不能用作独立性验证。

| 页面 | 一级 | 二级 | 三级 | 严格限制 |
|---|---|---|---|---|
| 作业 0：WU 未来 24 小时 | 渲染 `wunderground.com/hourly/.../ICAO`，取逐小时表 | 抓取公开 HTML 中结构化状态/表格并核验页面日期 | Open-Meteo 仅作为**另标注的模型兜底** | WU 未取得完整逐小时表时写 `null`；不能用日摘要补全 |
| 答案 1：WU 历史 | 渲染三个或四个 `history/daily/.../date/YYYY-M-D` 页面 | 抓静态日表，保留实际间隔 | AWC METAR 或 IEM 历史 METAR，明确不是 WU | WU 无数值云量时 `cloud_cover_pct=null`，仅保留 `condition_text` |
| 作业 1：TAF | AWC `https://aviationweather.gov/api/data/taf?ids=ICAO` 当前原文 | Ogimet 历史表单（UTC 范围，存 TXT/HTML） | AALTROnav 日期页/人工原文 | 仅提取 `TXnn/DDHHZ`、`TNnn/DDHHZ`；无 72 小时归档即标不可用 |
| 答案 2：METAR | AWC JSON：`/api/data/metar?ids=ICAO&format=json&taf=false&hours=72` | IEM：`/cgi-bin/request/asos.py?network=...&station=ICAO...` | WU/Metar-Taf.com 网页人工校对 | AWC/IEM 无数值降水时填 `null`；云况保留 `FEW/SCT/BKN/OVC/CAVOK`，不换算百分比 |
| 作业 2–6：Open-Meteo | Historical Forecast API + Forecast API 显式模型 | Single Runs/归档证据重试并存运行元数据 | 上游公开模式文件另建 GRIB 链；网页人工核验 | 不能用其他模型补齐；`best_match` 不是固定单一模型 |

Open-Meteo 依次请求 `ecmwf_ifs`、`ecmwf_aifs025_single`、`gfs_seamless`、`icon_seamless` 和无 `models` 的 `best_match`。历史端点为 `https://historical-forecast-api.open-meteo.com/v1/forecast`；未来端点为 `https://api.open-meteo.com/v1/forecast`。

## 工作流

1. 运行 `scripts/fetch_weather_bundle.py` 一次性请求 Open-Meteo 五模型、AWC METAR、AWC 当前 TAF、IEM，并保存所有成功与失败响应。
2. 对 WU 作业 0 与答案 1 用渲染浏览器取表。先核对显示日期、站名/ICAO、当地时区和抓取锚点。只出现摘要、日期不一致或字段不足时，必须标记失败而非输出虚假的 24 小时序列。
3. 如需过去 72 小时发布 TAF，使用 Ogimet 表单。把当地窗口换为 UTC，保存 `display_metars2.php` 的完整 URL 与 TXT/HTML。返回空页或无 TAF 时，只保留当前 TAF 的作业 1 结果并把历史项标为 `null`。
4. 运行 `scripts/normalize_weather_bundle.py`。它每模型严格截取 72 条历史整点和 24 条未来整点，输出 CSV、网格元数据、METAR 实际观测、请求状态和覆盖审计。
5. 以覆盖审计核对每个指定模型是否均为 `72/72` 与 `24/24`，检查原始 `null` 是否仍为 `null`。一个模型失败只影响自己的作业，绝不跨模型补齐。
6. 用规范化 CSV 生成 HTML。每个区块按“血缘声明、元数据、数据正文、缺失说明、原始 URL”排列。时间主键用带时区的 ISO 8601；展示标题显式写 UTC+8。

## 固定输出顺序

按此顺序提供：`作业 0（WU 未来）`、`作业 1（TAF）`、`作业 2（ECMWF IFS）`、`作业 3（ECMWF AIFS）`、`作业 4（GFS）`、`作业 5（ICON）`、`作业 6（best_match）`、`答案 1（WU 历史）`、`答案 2（METAR）`。

模式作业必须记录请求模型、实际返回的网格纬度/经度、海拔、返回时区/单位、抓取时间和完整 URL。没有来自接口响应或官方资料的分辨率信息时，写“未在本次响应确认”。

## 已验证的 ZGGG 运行

ZGGG（23.3933°N, 113.3083°E）实测可得到五个 Open-Meteo 模型各 72 条历史整点和 24 条未来整点，字段含温度、降水、雨量与分层云量。AWC METAR 成功返回实际约 30 分钟间隔记录。AWC 当前 TAF 最小参数请求成功；`format=raw` 被拒绝，`format=json&hours=72` 在该次运行 HTTP 504。因此，只有成功取到的数据可称“成功”；历史 TAF 或 WU 分时页失败时必须照实报告。

## 资源

- `scripts/fetch_weather_bundle.py`：请求并保存原始 API 证据。
- `scripts/normalize_weather_bundle.py`：无插值规范化、单位转换和覆盖审计。
- `references/source-strategy.md`：来源能力、血缘、限制与 URL。
- `templates/dashboard_template.html`：简洁看板的字段与样式骨架。
