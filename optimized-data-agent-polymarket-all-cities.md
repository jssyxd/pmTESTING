# Polymarket Weather 城市最高温与最低温数据代理（反幻觉加固版 v2）

本任务仅用于**客观天气数据采集、数据血缘治理和预测研究**，不构成任何下注、交易或资金操作建议。严格按城市列表顺序独立处理；不得将一个城市、一个模式或一个聚合页面的数据移植到另一城市、另一模式或另一来源。

**反幻觉铁律（v2 新增，优先级最高）：** 文档里的每一个数字、URL、状态码、时间都必须能追溯到同城证据目录下已落盘的原始文件；禁止在原始响应落盘之前起草任何数据区块；禁止手写 meta 文件、校验和、审计 JSON 或事件 URL；禁止把"校验通过/抓取成功"当作输出证据。grok 审阅曾对一份交付判"不合格"：752 个原始响应路径零落盘、best_match 表与其他模型逐字节相同、188 处占位符 URL、作业 0 声称成功却 0 行输出——本版提示词从结构上堵死这四类幻觉。

## 第 0 步（每轮运行最先执行）：Polymarket 事件快照

1. 在拉取任何天气数据**之前**，调用 `scripts/fetch_polymarket_snapshot.py`（或等价实现）抓取 Polymarket 公开天气事件接口，保存原始响应到 `raw/polymarket_snapshot.json` 及侧车 `raw/polymarket_snapshot.json.meta.json`（meta 必须含 `url`、`status`、`fetched_at_utc`、`bytes`、`sha256`，由脚本在保存时写入，禁止文档阶段补写）。
2. 从快照解析每城最高/最低气温事件：事件 URL、结算日（UTC）、市场类型、事件描述原文关键句。**引用句必须与快照文件字符串逐字一致**；解析结果写为每城第 0 步块（见"每个城市文档的固定结构"）。
3. 快照抓取失败（HTTP 非 200 / 空 JSON / 超时）时：该城事件行全部写 `null`，页头事件字段写"未取得事件 URL（原因、尝试时间 UTC、证据文件路径）"，并记录尝试时间；**禁止**用旧城市表、记忆或猜测补事件 URL，禁止手填链接。
4. 事件下架、结算规则或 WU 结算站变更时，以当前事件原文为准并更新城市清单，记录差异；不得沿用旧城市表猜测。城市清单表中"最高气温项目/最低气温项目"列以第 0 步快照为准，快照缺失时整列 `null`。

## 当前市场快照与结算边界

本城市表基于 Polymarket 公开天气事件接口在 **2026-08-20T19:57:41.323774+00:00** 的开放项目快照生成：温度事件城市共 51 个，其中 **47 个**以 Weather Underground 的 **Daily Observations** 表结算，均已列入下方清单，并且当前分别至少有一个最高气温和一个最低气温项目。每次自动运行前，必须执行第 0 步重新读取当前开放事件和事件描述；市场下架、结算规则或 WU 结算站变更时，以当前事件原文为准并更新清单，不能沿用旧城市表猜测。

> **结算优先级。**对 WU 城市，Polymarket 事件描述指定的 WU Daily Observations 表是最高/最低气温的结算依据；Day High & Low 摘要不能代替该表。对非 WU 结算城市，不得创建 WU 数据页来替代其官方结算源。

## 城市清单：仅 Weather Underground Daily Observations 结算

| 序号 | 城市 | 时区（结算站当地 IANA） | WU 结算站 / ICAO | WU Daily Observations 结算页 | 精确坐标 | 最高气温项目 | 最低气温项目 |
|---:|---|---|---|---|---|---|---|
| 1 | 上海 | Asia/Shanghai | Shanghai/Pudong Intl / ZSPD | https://www.wunderground.com/history/daily/cn/shanghai/ZSPD | 31.146000°N, 121.800000°E | 见第 0 步快照 | 见第 0 步快照 |
| 2 | 东京 | Asia/Tokyo | Tokyo/Haneda Intl / RJTT | https://www.wunderground.com/history/daily/jp/tokyo/RJTT | 35.553000°N, 139.781000°E | 见第 0 步快照 | 见第 0 步快照 |
| 3 | 丹佛 | America/Denver | Buckley SFB / KBKF | https://www.wunderground.com/history/daily/us/co/aurora/KBKF | 39.713000°N, 104.758000°W | 见第 0 步快照 | 见第 0 步快照 |
| 4 | 亚特兰大 | America/New_York | Atlanta/Hartsfield-Jackson Intl / KATL | https://www.wunderground.com/history/daily/us/ga/atlanta/KATL | 33.629720°N, 84.442230°W | 见第 0 步快照 | 见第 0 步快照 |
| 5 | 休斯顿 | America/Chicago | Houston/Hobby Arpt / KHOU | https://www.wunderground.com/history/daily/us/tx/houston/KHOU | 29.645820°N, 95.282140°W | 见第 0 步快照 | 见第 0 步快照 |
| 6 | 伦敦 | Europe/London | London City Arpt / EGLC | https://www.wunderground.com/history/daily/gb/london/EGLC | 51.505000°N, 0.055000°E | 见第 0 步快照 | 见第 0 步快照 |
| 7 | 勒克瑙 | Asia/Kolkata | Lucknow/Singh Arpt / VILK | https://www.wunderground.com/history/daily/in/lucknow/VILK | 26.761000°N, 80.889000°E | 见第 0 步快照 | 见第 0 步快照 |
| 8 | 北京 | Asia/Shanghai | Beijing Intl / ZBAA | https://www.wunderground.com/history/daily/cn/beijing/ZBAA | 40.082000°N, 116.603000°E | 见第 0 步快照 | 见第 0 步快照 |
| 9 | 华沙 | Europe/Warsaw | Warsaw/Chopin Arpt / EPWA | https://www.wunderground.com/history/daily/pl/warsaw/EPWA | 52.163000°N, 20.961000°E | 见第 0 步快照 | 见第 0 步快照 |
| 10 | 卡拉奇 | Asia/Karachi | Karachi/Jinnah Intl / OPKC | https://www.wunderground.com/history/daily/pk/karachi/OPKC | 24.902000°N, 67.139000°E | 见第 0 步快照 | 见第 0 步快照 |
| 11 | 台北 | Asia/Taipei | Taipei/Songshan Arpt / RCSS | https://www.wunderground.com/history/daily/tw/taipei/RCSS | 25.069000°N, 121.552000°E | 见第 0 步快照 | 见第 0 步快照 |
| 12 | 吉达 | Asia/Riyadh | Jeddah/King Abdulaziz Intl / OEJN | https://www.wunderground.com/history/daily/sa/jeddah/OEJN | 21.685000°N, 39.166000°E | 见第 0 步快照 | 见第 0 步快照 |
| 13 | 吉隆坡 | Asia/Kuala_Lumpur | Kuala Lumpur Intl / WMKK | https://www.wunderground.com/history/daily/my/sepang-district/WMKK | 2.747000°N, 101.714000°E | 见第 0 步快照 | 见第 0 步快照 |
| 14 | 圣保罗 | America/Sao_Paulo | Sao Paulo Intl / SBGR | https://www.wunderground.com/history/daily/br/guarulhos/SBGR | 23.432000°S, 46.469000°W | 见第 0 步快照 | 见第 0 步快照 |
| 15 | 墨西哥城 | America/Mexico_City | Mexico City Intl / MMMX | https://www.wunderground.com/history/daily/mx/mexico-city/MMMX | 19.436000°N, 99.072000°W | 见第 0 步快照 | 见第 0 步快照 |
| 16 | 多伦多 | America/Toronto | Toronto/Pearson Intl / CYYZ | https://www.wunderground.com/history/daily/ca/mississauga/CYYZ | 43.679000°N, 79.629000°W | 见第 0 步快照 | 见第 0 步快照 |
| 17 | 奥斯汀 | America/Chicago | Austin/Bergstrom Intl / KAUS | https://www.wunderground.com/history/daily/us/tx/austin/KAUS | 30.183100°N, 97.680630°W | 见第 0 步快照 | 见第 0 步快照 |
| 18 | 安卡拉 | Europe/Istanbul | Ankara/Esenboğa Intl / LTAC | https://www.wunderground.com/history/daily/tr/%C3%A7ubuk/LTAC | 40.128000°N, 32.995000°E | 见第 0 步快照 | 见第 0 步快照 |
| 19 | 巴拿马城 | America/Panama | Panama/Gelabert Intl / MPMG | https://www.wunderground.com/history/daily/pa/panama-city/MPMG | 8.967000°N, 79.555000°W | 见第 0 步快照 | 见第 0 步快照 |
| 20 | 巴黎 | Europe/Paris | Paris/Le Bourge Arpt / LFPB | https://www.wunderground.com/history/daily/fr/bonneuil-en-france/LFPB | 48.967000°N, 2.428000°E | 见第 0 步快照 | 见第 0 步快照 |
| 21 | 布宜诺斯艾利斯 | America/Argentina/Buenos_Aires | Buenos Aires/Pistarini Arpt / SAEZ | https://www.wunderground.com/history/daily/ar/ezeiza/SAEZ | 34.822000°S, 58.536000°W | 见第 0 步快照 | 见第 0 步快照 |
| 22 | 广州 | Asia/Shanghai | Guangzhou/Baiyun Intl / ZGGG | https://www.wunderground.com/history/daily/cn/guangzhou/ZGGG | 23.392000°N, 113.307000°E | 见第 0 步快照 | 见第 0 步快照 |
| 23 | 开普敦 | Africa/Johannesburg | Capetown Intl / FACT | https://www.wunderground.com/history/daily/za/matroosfontein/FACT | 33.965000°S, 18.602000°E | 见第 0 步快照 | 见第 0 步快照 |
| 24 | 惠灵顿 | Pacific/Auckland | Wellington Intl / NZWN | https://www.wunderground.com/history/daily/nz/wellington/NZWN | 41.331000°S, 174.806000°E | 见第 0 步快照 | 见第 0 步快照 |
| 25 | 慕尼黑 | Europe/Berlin | Munich Intl / EDDM | https://www.wunderground.com/history/daily/de/munich/EDDM | 48.348000°N, 11.813000°E | 见第 0 步快照 | 见第 0 步快照 |
| 26 | 成都 | Asia/Shanghai | Chengdu/Shuangliu Intl / ZUUU | https://www.wunderground.com/history/daily/cn/chengdu/ZUUU | 30.576000°N, 103.950000°E | 见第 0 步快照 | 见第 0 步快照 |
| 27 | 新加坡 | Asia/Singapore | Singapore/Changi Intl / WSSS | https://www.wunderground.com/history/daily/sg/singapore/WSSS | 1.368000°N, 103.982000°E | 见第 0 步快照 | 见第 0 步快照 |
| 28 | 旧金山 | America/Los_Angeles | San Francisco Intl / KSFO | https://www.wunderground.com/history/daily/us/ca/san-francisco/KSFO | 37.619610°N, 122.365610°W | 见第 0 步快照 | 见第 0 步快照 |
| 29 | 武汉 | Asia/Shanghai | Wuhan/Tianhe Intl / ZHHH | https://www.wunderground.com/history/daily/cn/wuhan/ZHHH | 30.783000°N, 114.205000°E | 见第 0 步快照 | 见第 0 步快照 |
| 30 | 洛杉矶 | America/Los_Angeles | Los Angeles Intl / KLAX | https://www.wunderground.com/history/daily/us/ca/los-angeles/KLAX | 33.938170°N, 118.386600°W | 见第 0 步快照 | 见第 0 步快照 |
| 31 | 济南 | Asia/Shanghai | Jinan Yaoqiang Intl / ZSJN | https://www.wunderground.com/history/daily/cn/jinan/ZSJN | 36.856000°N, 117.206000°E | 见第 0 步快照 | 见第 0 步快照 |
| 32 | 深圳 | Asia/Shanghai | Shenzhen/Boan Intl / ZGSZ | https://www.wunderground.com/history/daily/cn/shenzhen/ZGSZ | 22.639000°N, 113.803000°E | 见第 0 步快照 | 见第 0 步快照 |
| 33 | 米兰 | Europe/Rome | Milan/Malpensa Arpt / LIMC | https://www.wunderground.com/history/daily/it/milan/LIMC | 45.631000°N, 8.728000°E | 见第 0 步快照 | 见第 0 步快照 |
| 34 | 纽约市 | America/New_York | New York/La Guardia Arpt / KLGA | https://www.wunderground.com/history/daily/us/ny/new-york-city/KLGA | 40.779450°N, 73.880270°W | 见第 0 步快照 | 见第 0 步快照 |
| 35 | 芝加哥 | America/Chicago | Chicago/O'Hare Intl / KORD | https://www.wunderground.com/history/daily/us/il/chicago/KORD | 41.960170°N, 87.931610°W | 见第 0 步快照 | 见第 0 步快照 |
| 36 | 西雅图 | America/Los_Angeles | Seattle-Tacoma Intl / KSEA | https://www.wunderground.com/history/daily/us/wa/seatac/KSEA | 47.444670°N, 122.314420°W | 见第 0 步快照 | 见第 0 步快照 |
| 37 | 赫尔辛基 | Europe/Helsinki | Helsinki/Vantaa Arpt / EFHK | https://www.wunderground.com/history/daily/fi/vantaa/EFHK | 60.327000°N, 24.957000°E | 见第 0 步快照 | 见第 0 步快照 |
| 38 | 达拉斯 | America/Chicago | Dallas/Love Fld / KDAL | https://www.wunderground.com/history/daily/us/tx/dallas/KDAL | 32.838360°N, 96.835840°W | 见第 0 步快照 | 见第 0 步快照 |
| 39 | 迈阿密 | America/New_York | Miami Intl / KMIA | https://www.wunderground.com/history/daily/us/fl/miami/KMIA | 25.788060°N, 80.316920°W | 见第 0 步快照 | 见第 0 步快照 |
| 40 | 郑州 | Asia/Shanghai | Zhengzhou/Xinzheng Arpt / ZHCC | https://www.wunderground.com/history/daily/cn/zhengzhou/ZHCC | 34.520000°N, 113.834000°E | 见第 0 步快照 | 见第 0 步快照 |
| 41 | 重庆 | Asia/Shanghai | Chongqing/Jiangbei Intl / ZUCK | https://www.wunderground.com/history/daily/cn/chongqing/ZUCK | 29.718000°N, 106.639000°E | 见第 0 步快照 | 见第 0 步快照 |
| 42 | 釜山 | Asia/Seoul | Busan/Gimhae Intl / RKPK | https://www.wunderground.com/history/daily/kr/busan/RKPK | 35.179000°N, 128.938000°E | 见第 0 步快照 | 见第 0 步快照 |
| 43 | 阿姆斯特丹 | Europe/Amsterdam | Amsterdam/Schiphol Arpt / EHAM | https://www.wunderground.com/history/daily/nl/schiphol/EHAM | 52.315000°N, 4.790000°E | 见第 0 步快照 | 见第 0 步快照 |
| 44 | 青岛 | Asia/Shanghai | Qingdao/Jiaodong Arpt / ZSQD | https://www.wunderground.com/history/daily/cn/qingdao/ZSQD | 36.362000°N, 120.087000°E | 见第 0 步快照 | 见第 0 步快照 |
| 45 | 首尔（仁川） | Asia/Seoul | Seoul/Incheon Intl / RKSI | https://www.wunderground.com/history/daily/kr/incheon/RKSI | 37.469000°N, 126.451000°E | 见第 0 步快照 | 见第 0 步快照 |
| 46 | 马尼拉 | Asia/Manila | Manila/Aquino Intl / RPLL | https://www.wunderground.com/history/daily/ph/manila/RPLL | 14.507000°N, 121.004000°E | 见第 0 步快照 | 见第 0 步快照 |
| 47 | 马德里 | Europe/Madrid | Madrid/Barajas Arpt / LEMD | https://www.wunderground.com/history/daily/es/madrid/LEMD | 40.466000°N, 3.555000°W | 见第 0 步快照 | 见第 0 步快照 |

每个保留城市均同时处理**最高气温**和**最低气温**市场。例如，上海文档必须识别"上海最高气温"和"上海最低气温"；巴黎文档必须识别"巴黎最高气温"和"巴黎最低气温"。二者共享同一 WU 结算站，但必须分别在页头注明当天实际对应的 Polymarket 事件 URL（取自第 0 步快照）、结算日和市场类型，不能把最高/最低温互相代替。

## 输出与不可变规则

对每个城市在 `每日数据/` 下创建一个独立 Markdown 文件。文件名必须为 `YYYY-MM-DD-HH-mm-城市-ICAO.md`，例如 `2026-08-19-22-30-上海-ZSPD.md`。页面时间主键使用该城市结算站的 **IANA 当地时区**，并在页头同时保存 UTC 抓取时间。日期边界以结算站当地日历日为准，而不是统一 UTC+8。模型页以抓取时刻向下取整到整点为锚点：历史窗口为锚点前 72 个已结束整点，未来窗口为锚点后 24 个尚未来临整点。

**时间窗（Open-Meteo 请求参数）：** 历史与未来请求的 `start_date`/`end_date` 必须使用**结算站当地日历日**（历史 = 锚点前 72 小时所在当地日 至 锚点所在当地日；未来 = 锚点所在当地日 至 锚点后 24 小时所在当地日，均含起止日整日），不得为全城共用一组固定 UTC 日期。API 的 `timezone` 参数必须传该城结算站当地 IANA。

每个区块都必须以以下格式开头，并将方括号替换为真实值：

> **强制数据血缘声明：**本轮使用的观测源是[来源或无]，模型源是[模型名或无]，API/网页层是[服务]；是否存在上下游依赖：[说明]。本页不把同源展示层或聚合层误视为独立观测样本。

随后依次写入页头元数据、数据正文和缺失说明。页头必须记录：结算站当地抓取时间（IANA）、UTC 抓取时间、**锚点时刻**、**本城首次请求 ts 至末次请求 ts（取自同城 raw meta 的 `fetched_at_utc`，不得引用全轮日志范围）**、**本城最高/最低气温 Polymarket 事件 URL、结算日、市场类型（见第 0 步快照；快照缺失写 null+原因）**、**解析后的实际请求 URL（每源一条，从 raw meta 注入；禁止 `{country}`/`{city}`/`ids=ICAO` 等字面占位符）**、参数、HTTP 状态、响应时间戳/报文时间、模型请求名、API 实际返回的网格坐标、海拔、**温度单位的原生性**、原始响应文件路径（**相对路径**，`raw/…` 或 `openmeteo/…`）和单位证据引用（如 metric≡english 字节比对结果，引用 `wu_daily_unit_compare.json` 行）。模型页必须明确标为"数值模式预报/历史预报，非机场观测"。

## 温度单位：只保留来源原生值

**禁止自行换算温度。**每个数据区块固定设置"原生 ℃"和"原生 ℉"两个独立字段，但只有源端实际显示或 API 实际返回该单位时才写值；未从该来源获得的单位写 `null`，不得以 `℃ × 9/5 + 32` 或其他公式补出。

Weather Underground 的结算依据是页面 **Daily Observations** 表，而不是 Day High & Low 摘要。对 WU 的历史答案和作业 0，分别抓取同一站点、同一时次、同一日期下的原生摄氏度视图与原生华氏度视图；两份视图必须各自保存 URL、抓取时间与原文证据。**每次抓取后立即计算两视图各自 `sha256` 并写入逐日比对文件 `raw/wu_daily_unit_compare.json`**（字段：date、metric_sha256、english_sha256、bytes_equal、注）；文档中"两视图一致/不一致"的声明必须引用该文件的具体行。只有时间戳精确匹配时才在同一行同时写两列，否则不匹配的一列写 `null`。WU 的数值应逐字保留，不能从另一单位推算。已知限制（2026-08-21 实测）：WU 公开页对 `cm_units`/`units` 参数及单位 cookie 均返回字节一致页面，原生 ℉ 视图不可得——此时 `wu_daily_unit_compare.json` 的 `bytes_equal=true` 即证据，℉ 列写 `null` 并在缺失说明引用该文件；**禁止**在无比对产物的情况下声称"两视图一致"，也**禁止**声称取得了原生 ℉。

对 Open-Meteo、TAF、METAR 和其他来源，不得把服务端单位参数返回、客户端格式化或本地公式转换误称为模型原生双单位。如果该次保存的原始响应仅含 `°C`，则"原生 ℉"列写 `null`；若原始响应明确同时含两个单位，才各自写入。原始值为 `null` 时，两个温度字段均写 `null`。严禁插值、前后填充、均值填充、模型间替代、以 METAR 代替模式，或把天气文字推导为数值降水/云量。降水、雨量和云量未由该原始模型提供时都写 `null`。

## 固定作业顺序

每个城市文档按下列顺序输出。不要重新编号；即使某一作业失败也保留该作业页，并记录失败原因、尝试时间（UTC，取自请求完成时刻）和证据位置（raw meta 文件路径）。

| 顺序 | 区块 | 专属来源 / 模型参数 | 本次验证状态与执行规则 |
|---:|---|---|---|
| 答案 | Weather Underground 历史观测 | 三至四个历史日页 | 仅输出已抓到的实际观测时间。公开页无数值云量则 `cloud_cover_pct=null`。WU 与可能复用同一航空观测链的 METAR 网页不可计为独立观测。页头与每日期行必须给出解析后的实际 URL（从 meta 注入）。 |
| 作业 0 | WU Hourly Forecast for Today | `https://www.wunderground.com/hourly/<country>/<city>/<ICAO>`（解析后） | **二选一**：(a) 解析验证页面小时表结构（定位小时表容器、统计独立小时行、核对日期一致）通过后，在文档内物化全部小时行（行=小时，列=温度 ℃/℉、条件），元数据写明实际字节数、`sha256`、表内行数、首末小时与日期一致性结论；(b) 解析失败或表不完整，则全部小时字段写 `null` + 失败原因 + 尝试时间。"页面抓取成功/字节数校验通过"**不作为成功证据**；不得以日摘要或 Open-Meteo 冒充 WU。 |
| 作业 1 | TAF 历史报文 | AWC 当前 TAF → Ogimet 历史 TAF → 其他公开航空档案 | **只取 TAF，不得用 METAR 代替。**提取过去 72 小时内发布报文的原始 `TXnn/DDHHZ` / `TNnn/DDHHZ`，保留原报文的 UTC 时间与结算站当地 IANA 时间转换；有效期 `DDHH/DDHH` 解析为 `YYYY-MM-DDTHH:MMZ`（原文含即须填，无 TX/TN 不代表无有效期）。不构造逐小时序列。无历史 TAF 原文时明确写 `null` + 尝试时间。Ogimet 已知 404（2026-08-21 起，94/94，273 字节错误页）：保留为已知限制记录（带日期范围），每轮仅发 1 次探针；探针通过当轮立即恢复全量抓取；探针结果（状态、时间）写入 TAF 页。 |
| 作业 2 | ECMWF IFS HRES | `models=ecmwf_ifs` | 已验证 ZGGG 72/72 历史、24/24 未来和目标变量非空。工作簿标签为 IFS HRES（约 9 km）；仍以本次 API 返回网格点为准。 |
| 作业 3 | ECMWF AIFS 0.25° Single | `models=ecmwf_aifs025_single` | 已验证 ZGGG 72/72、24/24、目标变量非空。工作簿标注 0.25°（约 25 km），6 小时更新；不得假定某一单一运行，记录 API 返回证据。 |
| 作业 4 | NOAA GFS | `models=gfs_seamless` | 已验证原作业链路。此为无缝组合参数；若要与工作簿 GFS Global 直接对照，参见作业 8 的 `ncep_gfs_global`，二者同属 NOAA，不构成独立观测。 |
| 作业 5 | DWD ICON | `models=icon_seamless` | 已验证原作业链路。此为无缝组合参数；若要与工作簿 ICON Global 直接对照，参见作业 7 的 `dwd_icon_global`，二者同属 DWD，不构成独立观测。 |
| 作业 6 | best_match | 不传 `models` | 已验证原作业链路。自动选择模型并非固定单一来源；必须保存实际返回网格点，不能宣称固定分辨率、固定上游或独立样本。**响应体不含 `model` 字段，路由身份不可从响应体证明**；页面缺失说明必须写明"API 响应未返回模型标识（`api_returned_model=null`），本页仅以返回网格点与原始文件为证据，不得宣称该站 best_match 即某固定模型"；当返回网格与数值和某同网格模型一致时，写明该巧合并保留字节不同的原始文件作为唯一身份证据；**数值相同不是复制证据，字节逐位相同才是**。 |
| 作业 7 | DWD ICON Global | `models=dwd_icon_global` | 已验证 72/72、24/24、温度/降水/云量非空。工作簿标注 0.1°（约 11 km）、逐小时。 |
| 作业 8 | NOAA GFS Global | `models=ncep_gfs_global` | 已验证 72/72、24/24、温度/降水/云量非空。工作簿标注 0.11°（约 13 km）、逐小时。GFS Pressure Variables 是同一模式的变量集，不另建温度作业。 |
| 作业 9 | ECMWF IFS 0.25° | `models=ecmwf_ifs025` | 已验证 72/72、24/24、温度/降水/云量非空。工作簿标注 0.25°（约 25 km）。不要用作业 2 的 HRES 值填补。 |
| 作业 10 | Météo-France ARPEGE World | `models=arpege_world` | 已验证 72/72、24/24、温度/降水/云量非空。工作簿标注 0.25°（约 25 km）、逐小时。 |
| 作业 11 | UKMO Global | `models=ukmo_global_deterministic_10km` | 已验证 72/72、24/24、温度/降水/云量非空。工作簿标注约 0.09°（约 10 km）。 |
| 作业 12 | JMA GSM | `models=jma_gsm` | 已验证 72/72、24/24、温度/降水/云量非空。工作簿标注 0.5°（约 55 km）、6 小时更新。 |
| 作业 13 | Canadian GEM Global | `models=gem_global` | 已验证 72/72、24/24、温度/降水/云量非空。工作簿标注 0.15°（约 15 km）、3 小时。 |
| 作业 14 | CMA GFS GRAPES | `models=cma_grapes_global` | 已验证 72/72、24/24、温度/降水/云量非空。工作簿标注 0.125°（约 15 km）、3 小时。 |
| 作业 15 | NOAA AIGFS | `models=ncep_aigfs025` | 已验证 72/72、24/24、温度/降水/云量非空。工作簿标注 0.25°（约 25 km）、6 小时。 |
| 作业 16 | NOAA HGEFS ensemble mean | `models=ncep_hgefs025_ensemble_mean` | 已验证 72/72、24/24、温度/降水/云量非空。页面必须写明这是集合平均，不能当作单一确定性模式。 |
| 答案 2 | METAR 实况 | AWC API → IEM → 网页人工校验 | 只输出实际观测时刻而非人工整点。数值降水不存在则 `null`；云层保留 `FEW/SCT/BKN/OVC/CAVOK` 等类别与层高，不换算为云量百分比。 |

## 覆盖审计记录（每城必出，放在答案 2 之前）

**规则：状态列必须以本轮实际请求结果驱动；禁止在模板里硬编码 HTTP 状态与行数。** 未请求的条目写"未请求"，并引用带日期的验证记录；宁缺毋滥，缺行比假行安全。

| 模型/源 | 请求状态 | 返回行数 | 判定 | 依据（URL/网格/原始文件/验证记录） | 本轮尝试时间 UTC（未请求则填"未请求"+引用验证记录日期） |
|---|---|---|---|---|---|
| `ecmwf_ifs04` | [未请求/实测] | [— / 72/24] | 字段不可用（全 null） | 引用 `references/zggg-jobs-2-16-validation-2026-08-20.md`（2026-08-20 验证）或本轮原始文件 | [时间或"未请求"] |
| `bom_access_global` | [未请求/实测] | [— / 72/24] | 字段不可用（全 null） | 同上 | [时间或"未请求"] |
| 区域模型（ICON-EU、ICON-D2、HRRR、NAM、NBM、ARPEGE Europe、AROME France、AROME France HD、UKMO UKV、JMA MSM、MET Nordic、GEM Regional、HRDPS Continental、ARPAE ICON 2I、DMI/KNMI HARMONIE、MeteoSwiss ICON CH1/CH2） | [未请求/实测] | [—] | 地域排除 / 未覆盖 | **必须以本轮实际请求（或显式"未请求+理由"）为依据**，逐城说明；不得凭坐标清单机械套用他城结论 | [时间或"未请求"] |

**地域排除铁律：** 2026-08-20/21 实测 `jma_gsm`、`cma_grapes_global`、`ncep_hgefs025_ensemble_mean` 在丹佛 KBKF、惠灵顿 NZWN 等非中国坐标均返回完整非空数据，旧"非中国坐标必 null"结论**不得沿用**。对台北、新加坡和马尼拉等非中国坐标，每次运行都必须重新实测区域模型覆盖后再判定。任何判定都不得伪造请求、伪造 `null` 序列或将区域模式误用到中国。

## 每个城市文档的固定结构

```markdown
---
# [城市] 最高气温与最低气温数据（[ICAO]）

> **强制数据血缘声明：**…（全文档总声明，引用第 0 步快照与各区块）

- 抓取时间（UTC+8 显示；UTC 存储）：[实际运行区间：本城首次请求 ts → 末次请求 ts]
- 锚点：[…Z]
- 第 0 步：Polymarket 事件快照
  | 市场 | 事件 URL | 结算日（UTC） | 市场类型 | 事件描述原文关键句 |
  |---|---|---|---|---|
  | 最高气温 | [快照中 URL；快照失败写 null+原因] | … | … | [与快照文件逐字一致] |
  | 最低气温 | … | … | … | … |
- 快照文件：`raw/polymarket_snapshot.json`（+ meta）
---
```

## 每个模型页的固定模板

```markdown
---
## 【作业 N】[模型全称]

> **强制数据血缘声明：**本轮使用的观测源是无，模型源是[模型全称]，API 层是 Open-Meteo；是否存在上下游依赖：Open-Meteo 接入[供应方]数值模式，该数据为模式预报/历史预报，不是机场观测。

| 元数据 | 值 |
|---|---|
| 城市 / ICAO | [城市] / [ICAO] |
| 输入坐标 | [纬度], [经度] |
| API 返回网格点 / 海拔 | [latitude], [longitude] / [elevation] m |
| 模型请求参数 | `models=[模型参数]`（作业 6 写"不传 models"） |
| 抓取时间 | [UTC+8 显示]；[UTC]（取自 meta `fetched_at_utc`，即请求完成时刻，非锚点） |
| 历史窗口 | [72 小时起点] 至 [锚点，不含] |
| 未来窗口 | [锚点之后] 至 [24 小时终点，含] |
| 完整原始请求 | [实际请求 URL，从 meta 注入，禁止占位符] |
| 原始响应文件 | [相对路径：openmeteo/[ICAO]_[模型]_[history|forecast]_raw.json（+ meta）] |
| 模型标识 | 作业 6：`api_returned_model=null`，路由身份不可从响应体证明；其余作业：记录响应证据 |

| 当地时间（结算站当地 IANA） | 窗口 | 原生 2m 温度 ℃ | 原生 2m 温度 ℉ | 总降水 mm | 雨量 mm | 总云量 % | 低云 % | 中云 % | 高云 % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| [ISO8601] | 历史 72 小时 / 未来 24 小时 | [仅源端原生 ℃，否则 null] | [仅源端原生 ℉，否则 null] | [值或 null] | [值或 null] | [值或 null] | [值或 null] | [值或 null] | [值或 null] |

**缺失说明：**[无 / 列出原始字段、HTTP 错误、限流或覆盖不足；不得填补。引用证据文件路径；失败记录含尝试时间 UTC。]
---
```

## TAF 页的固定模板

```markdown
---
## 【作业 1】TAF 历史报文的 TX/TN 预报

> **强制数据血缘声明：**本轮使用的观测源是无，模型源是机场 TAF，API/网页层是[AWC / Ogimet / 其他档案]；是否存在上下游依赖：TAF 是机场预报报文，非 METAR 实况观测。

| 元数据 | 值 |
|---|---|
| ICAO | [ICAO] |
| 本地查询窗口 / UTC 窗口 | [UTC+8 显示] / [UTC] |
| 查询 URL 与参数 | [AWC 实际 URL（meta 注入）]；[Ogimet 实际 URL（meta 注入）或"已知限制：404，见下"] |
| 抓取时间 | [UTC+8 显示]；[UTC]（取自 meta） |
| 历史 TAF 结果 | [成功 / 无报文（尝试时间：…）/ 请求失败（HTTP_404，尝试时间：…，证据：raw/taf_ogimet_*.html.meta.json）] |
| Ogimet 已知限制 | [自 2026-08-21 起 404（bytes=273 错误页）；本轮探针：状态、时间；探针通过已恢复全量] |

| 报文发布时间 UTC | 有效期 UTC | 原始 TX/TN token | 原生温度 ℃ / 原生温度 ℉ | 预计时间 UTC → 结算站当地时间（IANA） | 原始报文摘录 |
|---|---|---|---:|---|---|
| [值或 null] | [解析 `DDHH/DDHH` 为 `YYYY-MM-DDTHH:MMZ`；原文有即须填] | `TX34/2107Z` / `TN27/2022Z` | [仅原报文明确提供的值或 null] | [UTC] / [结算站 IANA 当地 ISO8601] | [原文] |

**限制：**只展示原文存在的 TX/TN。不得根据风、云、降水或 METAR 推测最高/最低温；不得生成分小时 TAF 温度。
---
```

## 执行与失败规则

1. 每日执行时按城市表顺序处理，一个城市完成全部区块后再进入下一城市；不要并行混合不同城市的原始证据。Open-Meteo 模型并发请求数上限 **3**。
2. **原始证据先行**：任何数值写入文档之前，其来源的原始响应文件必须已落盘，且同目录侧车 meta 必须包含 `url`、`status`、`fetched_at_utc`、`bytes`、`sha256` 五个字段（由抓取脚本在保存时写入；**文档阶段禁止补写 meta**，发现缺失即报缺口并触发补抓）。`fetched_at_utc` 必须是请求完成时刻（与运行日志 ts 一致），锚点单独存 `anchor_utc`，二者不得混写。HTTP 非 200、超时、空 JSON、日期不匹配、变量全 `null` 或覆盖不足都要保存证据（原始错误体落盘，如 429 的 54 字节错误体、Ogimet 404 的 273 字节错误页）。
3. 对每个**可用模型**，覆盖审计必须为历史 `72/72`、未来 `24/24`。不足时在该模型页写 `数据不可用`，缺少的小时保留 `null`。
4. 对 WU、TAF、METAR 保持各自语义。WU 网页、METAR 实况与 TAF 预报不可互相替代；同一上游的展示层不可被视为独立样本。
5. `best_match`、`*_seamless` 和集合平均不是固定单一模式。必须记录 API 返回证据和真实网格点，不可把工作簿中的单一分辨率硬写到这些页面。best_match 必须写明"响应体不含 model 字段，路由身份不可从响应体证明"（见作业 6 行）。
6. 若实现自动执行，运行频率应为每天数次以内；任务只是脚本化公共 API 拉取时，采用可持续运行的确定性任务，而不是在每个小时启动完整智能代理。自动化配置、输出位置和失败重试必须另行明确，不在本提示词中假设已启用。
7. 完成一个城市文档后，确认每一页都遵循"血缘声明 → 页头元数据 → 数据正文 → 缺失说明"的固定结构，再写入最终文件。
8. **重试与超时**：所有网络请求必须实现"重试 + 指数退避"——对 SSL/连接超时、HTTP 429、5xx 自动重试（默认 3 次，退避 2s/5s/10s，可加抖动）；HTTP 404/400 属确定性失败，不重试，按已知限制记录。单请求：连接/握手超时 10–15s（快速失败），读超时分源（WU 60s、Open-Meteo/AWC 30s），禁止 90s 级超时拖住整城。每次重试尝试必须写日志（attempt 序号、时刻、状态、Retry-After 若存在）；失败尝试必须留痕（落盘 `<name>_attempt<N>_error.*` 或 meta `attempts:[{ts,status,error,bytes}]`），最终 raw 为最后一次成功响应。触发 429 时立即退避并降并发，不得以更高并发重试。
9. **完成信号**：每轮运行结束必须输出"取数缺口清单"（按来源×城市×模型聚合的失败计数与原因，如 `fetch_gaps` 字段），存在缺口时完成事件状态写 `complete_with_gaps`，**不得宣布无失败完成**；事件名保持既有词汇表（`PULL_COMPLETE` 等），不因缺口改名。
10. **交付门禁（最终文件写入前必跑）**：运行 `scripts/verify_doc_lineage.py`，检查 (a) 文档中每个"原始响应文件"相对路径在磁盘存在且非 0 字节、meta 五字段齐全；(b) 字面占位符零命中——token 清单 `{country}`、`{city}`、`{ICAO}`、`ids=ICAO`、`icao=ICAO`、`day=DD`、`month=MM`、`year=YYYY`、字面 `YYYY-MM-DD`（模板样式）；(c) 模型页行与 raw 数组全量比对、WU 页固定种子抽样比对（JSON 源字段比对，HTML 源解析后比对），产物 `doc_traceability_audit.json`。任一项不通过即该城未完成，重新生成对应页，**禁止手写审计产物**。审计脚本由抓取脚本体系自动执行，agent 只允许运行脚本。
11. **失败记录**：任何失败/缺口/重试都必须记录：原因、每次尝试时间（UTC，取自请求完成时刻）、最终状态、证据位置（raw meta 文件路径；pull_run.log 行号仅当次运行有效，可选）。禁止只写"失败"或"无报文"而不给时间与证据。
12. **断点续传**：续跑段必须在启动事件记录 `resume_from_idx` 与锚点；续跑时 `--anchor` 必填且必须与上次 `PULL_START` 的 `anchor_utc` 相等，不等即拒绝启动。完成判据为"最终 .md 存在 + 日志含该城 `city_done`"双条件。
13. **非 ASCII slug 属预期**（如安卡拉 `tr/%C3%A7ubuk`）：必须百分号编码后请求，不得跳过城市或改写 slug（改写会静默换站 = 数据污染）；所有文件读写强制 UTF-8。
14. **文档可追溯性**：模型页行 ↔ raw 数组的比对为全量（脚本生成场景两侧皆机器可读，全量比对成本≈抽样）；WU 页 HTML 解析脆弱，采用固定种子抽样（确定性、可复现）。

开始执行：先执行第 0 步（Polymarket 事件快照），再按照城市列表顺序独立处理全部城市，严格遵守以上作业顺序与数据治理规则，最后运行交付门禁。
