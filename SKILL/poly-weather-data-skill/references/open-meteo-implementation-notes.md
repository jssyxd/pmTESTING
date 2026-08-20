# Open-Meteo 官方仓库研读笔记

## 已核实的架构与数据血缘

Open-Meteo官方README说明其将国家气象机构公开发布的数值预报整合为统一API，并每日下载和处理超过2TB的模型数据。仓库中`Sources/App`按提供方拆分，包含ECMWF、GFS、CMA、DWD等独立域与变量定义；因此客户端请求必须显式保存API端点、`models`参数、响应`model`标识、请求URL、取得时间及落地坐标，不能把不同模型混为单一独立来源。来源：<https://github.com/open-meteo/open-meteo>。

## 历史预报与时间窗口

`ForecastapiController.swift`将`historicalForecast`类型的可用起点设为2016-01-01，默认逐小时输出，最多16日预报窗口；`forecast`类型的历史回溯仅到当前前93日。采集72小时历史预报时，应调用Historical Forecast API、固定`start_date`和`end_date`，禁止再混用`past_days`、`past_hours`、`forecast_days`或`forecast_hours`；源码明确将这些参数组合判定为不允许。

## 对齐、时区与坐标规则

查询解析器将逐小时范围按3600秒边界对齐，使用`timezone`请求参数解析显示时间；未设时区则以GMT返回。ZGGG数据治理必须固定`timezone=Asia/Shanghai`，同时保存响应中的`utc_offset_seconds`、`timezone`和ISO时间。源码也显示未指定`elevation`时API以DEM解析海拔，因此机场采集应同时保存请求坐标、API实际返回坐标与返回海拔，并标注网格点不等同机场传感器位置。

## 模型选择与变量语义

源码接受`models`数组，默认模型可由服务端的`best_match`替代；为了可回测性，天气市场工作流不能依赖默认路由，必须分别发起显式模型请求。ECMWF域代码确认`ecmwf_ifs025`对应0.25度IFS域，逐3小时、每6小时更新；CMA域代码确认`cma_grapes_global`为0.125度全球域，逐3小时、每6小时更新，且初始化后存在约4小时20分钟可用性延迟。若原生间隔不是逐小时，输出小时值可能涉及API插值；每条记录必须保留原生间隔与`temporal_resolution`。

ECMWF变量定义确认`temperature_2m`为摄氏度、`precipitation`为毫米、`cloud_cover`及低/中/高云量为百分比；代码还标明低/中/高云量在下载阶段计算。因而这些变量可用于天气型和升温抑制判断，但不能在模型变量缺失时用其他模型填补。`precipitation`与`rain`并不必然可互换；治理表应分列保存并附变量名、单位、模型和来源端点。

## 可执行采集规则

1. 对每个模型分别请求相同变量集合：`temperature_2m,precipitation,rain,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,weather_code`。
2. 请求使用显式`models=<模型标识>`、固定`timezone=Asia/Shanghai`和固定起止日期；当响应无小时字段、模型标识不匹配、时间点不连续、单位不符合或HTTP失败时，记录`data_unavailable`，不填补。
3. 分别保存原始响应和长表记录；长表主键至少为机场、有效时间UTC、展示时间UTC+8、来源端点、模型标识、变量、采集时间和请求哈希。
4. 用单独的观测表存WU/METAR；数值预报仅可与观测对齐后计算`Error = Observation - Model`，且同源显示层不得重复计作独立样本。

## 派生变量约束

`VariableHourly.swift`显示`rain`可由`precipitation`扣除雪水当量和（若存在）对流阵雨成分派生；`weather_code`则组合云量、降水、降雪、阵性降水、阵风、CAPE、能见度等输入推导。因此治理层必须保存请求变量名及“原始/派生”标记。模型返回`precipitation`并不等于单纯液态雨量；当`rain`或`weather_code`缺失时，应记录该模型字段不可用，而不是把另一个提供方的字段拼接进去。

## 官方端点路由

`ForecastapiController.swift`表明`/v1/forecast`是共用控制器，且`historical-forecast-api`、`previous-runs-api`、`single-runs-api`均为同一预测处理器的主机别名；提供方专用路由包括`/v1/ecmwf`（默认`ecmwf_ifs025`）、`/v1/cma`（默认`cma_grapes_global`）与`/v1/gfs`（默认GFS无缝路由）。对于可复现的回测，技能包将优先采用历史预报端点并显式传入模型，不使用`best_match`或提供方默认模型；只有在显式模型失败时才按预先声明的回退顺序尝试其他模型。
