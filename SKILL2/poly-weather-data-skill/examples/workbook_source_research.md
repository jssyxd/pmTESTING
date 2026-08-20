# 工作簿新增模型研究笔记

工作簿共列出 68 行（成对的模式名称/覆盖范围说明合并后为多类模式）。对 ZGGG 而言，明确全球且尚未在作业 2–6 中逐一作为专属模型拉取的候选为：Météo-France ARPEGE World、UKMO Global、JMA GSM、Canadian GEM Global、BOM ACCESS-G、CMA GFS GRAPES，以及 NOAA AIGFS/HGEFS。DWD ICON、NOAA GFS、ECMWF IFS/AIFS 已由作业 2–6 的显式模型请求覆盖。

工作簿中 ICON-EU、ICON-D2、HRRR、NAM、NBM、ARPEGE Europe、AROME France、UKMO UKV、JMA MSM、MET Nordic、GEM Regional、HRDPS、ARPAE、HARMONIE、MeteoSwiss ICON CH 等都有明确地域限制，不能覆盖广州；它们应列入“已逐一评估、因区域不覆盖 ZGGG 而排除”，而非进行伪请求。

Open-Meteo 当前官方 Forecast 文档的数据源表确认 ARPEGE、UKMO、GSM、GEM、ACCESS-G、GFS GRAPES 均有全球覆盖；文档说明模型会按地理范围与分辨率自动选择、不同模型可缺少变量或由原始时次插值至逐小时，且可通过 `models` 选择比较个别模型。官方源码确认可用域标识至少包括 `arpege_world`、`jma_gsm`、`gem_global`、`access_global`、`cma_grapes_global`，及 UKMO 的 `ukmo_global_deterministic_10km`。这些标识将在下一阶段以历史预报 API 与未来预报 API 实测，不以文档声明代替实际证据。

来源：
- /home/ubuntu/upload/工作簿1.xlsx
- https://open-meteo.com/en/docs
- https://github.com/open-meteo/open-meteo
