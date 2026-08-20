# 数据源策略与血缘参考

## Open-Meteo：模式预报层

| 用途 | 端点与模式 | 字段 | 血缘与限制 |
|---|---|---|---|
| 历史预报 | `historical-forecast-api.open-meteo.com/v1/forecast`；`ecmwf_ifs`、`ecmwf_aifs025_single`、`gfs_seamless`、`icon_seamless` 或默认 `best_match` | 2m 温度、总降水、雨量、总/低/中/高云量 | 是数值预报归档，不是机场观测。历史序列会拼接可用运行；每次保存请求 URL、返回网格点和时区。 |
| 当前/未来预报 | `api.open-meteo.com/v1/forecast`；同上 | 同上 | 为单独的未来请求保存证据。不能拿历史端点未来时段或当前端点过去时段冒充对方。 |

`best_match` 是自动选择，不是一个固定的单一模式。不要声称它具有统一的模式分辨率或独立于其他模式的观测血缘。返回纬度/经度可能与输入坐标不同，必须记录差异。

官方文档与源码研究见：https://open-meteo.com/en/docs/historical-forecast-api 和 https://github.com/open-meteo/open-meteo 。

## 航空气象：观测与预报分离

| 来源 | 作用 | 已验证能力 | 限制 |
|---|---|---|---|
| AWC | METAR 一级 API | `/api/data/metar?ids=ICAO&format=json&taf=false&hours=72` 可给 ZGGG 实际观测、温度、天气文字、分类云层 | 数值降水字段缺失即 `null`；云层是类别和层高，禁止变成百分比。 |
| AWC | 当前 TAF 一级 API | `/api/data/taf?ids=ICAO` 可取当前原始 TAF | 此端点取得的是当前报文，不能声称为 72 小时历史发布列表；实测 `format=raw` 被拒绝，`format=json&hours=72` 曾 504。 |
| IEM | 历史 METAR 二级 API | `cgi-bin/request/asos.py`，中国网络可列出 ZGGG | 历史集合基本无质量控制；该站明确非美国站点降水不可用，不能补降水。 |
| Ogimet | 历史 TAF/METAR 网页二级 | `metars.phtml.en` 支持 ICAO、UTC 时间范围和 TXT/HTML | 保存完整查询 URL/页面。空页、限流或无报文时，必须如实失败。页面自带仅供参考免责声明。 |
| UCAR/EOL 100.013 | 最终质控历史 METAR 归档三级 | 全球逐小时 METAR，月度 tar.bz2，final | 页面列出的覆盖截止 2026-05-31；不用于当前 72 小时。 |
| AALTROnav | 日期范围网页三级 | ICAO、开始/结束日期、METAR/TAF 类型表单 | 可能有登录或输出限制；先人工验证。 |
| Metar-TAF.com | 当前页面人工校对三级 | 当前 METAR 原文、温度、云况、天气现象 | 历史入口提示登录，不能假设免费自动化历史可用。 |

## Weather Underground：展示层

WU 分时未来页是作业 0，日历史页是答案 1。运行前检查页面日期、站点与时区。公开历史日页可显示实际观测间隔、温度、降水栏和天气状态；如无数值云量，云量百分比必须为 `null`，仅保留原始 `Condition` 文本。

WU 未来页若只显示日摘要、页面日期陈旧或逐小时表未渲染，不可将摘要填成 24 条小时数据。将本次 WU 作业标为失败并改用另标注的 Open-Meteo 模式数据作为分析辅助，而不是冒充 WU 结果。

WU、METAR-TAF.com 与部分航空展示数据可能从相近航空气象供应链获得，不能作为彼此独立的观测样本。

## TAF 的 TX/TN 解析

仅匹配原始电码中的 `TXnn/DDHHZ` 和 `TNnn/DDHHZ`。`M` 前缀表示负值。`DDHHZ` 是 UTC 日与小时；转换当地时间时保留原始 UTC token。多个 TN/TX 是原文事实，应逐项保留，不进行择优、平均或推测。

示例：`TX34/2107Z` 表示 34°C、UTC 21 日 07:00；在 UTC+8 站点为当地 21 日 15:00。此例的华氏温度可以按来源温度的单位基础转换为 93°F。

## 参考 URL

- https://www.clarmy.me/recommend-metar-data-sources/
- https://data.eol.ucar.edu/dataset/100.013
- https://www.ogimet.com/metars.phtml.en
- https://mesonet.agron.iastate.edu/request/download.phtml?network=CN__ASOS
- https://aaltronav.eu/weather/metar/
- https://metar-taf.com/zh/
- https://www.wunderground.com/hourly/cn/guangzhou/ZGGG
- https://www.wunderground.com/history/daily/cn/guangzhou/ZGGG/date/YYYY-M-D
