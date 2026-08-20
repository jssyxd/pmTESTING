#!/usr/bin/env python3
"""Render the Open-Meteo catalog validation JSON as a compact audit table."""

import argparse
import json
from pathlib import Path


def verdict(section: dict) -> str:
    return "pass" if section["http_status"] == 200 and section["target_variables_complete"] else "data_unavailable"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    rows = payload["catalog_results"]
    lines = [
        "# Open-Meteo 作业2–16逐项验证矩阵",
        "",
        f"- 机场：`{payload['airport_icao']}`；坐标：{payload['request_coordinate']['latitude']}, {payload['request_coordinate']['longitude']}`",
        f"- 历史窗口：{payload['history_window']['start_date']} 至 {payload['history_window']['end_date']}（预期72行）；未来窗口：{payload['forecast_window']['forecast_hours']}小时。",
        f"- 采集时间（UTC）：{payload['fetched_at_utc']}",
        "- 判定规则：历史和未来均需HTTP 200、行数分别为72/24且全部目标变量非空，否则为`data_unavailable`，不做填补。",
        "",
        "| 作业 | 模型ID | 类型 | 历史（HTTP/行数/判定） | 未来（HTTP/行数/判定） | 备注 |",
        "|---:|---|---|---|---|---|",
    ]
    for row in rows:
        history, forecast = row["history"], row["forecast"]
        note = "省略models，自动路由" if not row["models_parameter_sent"] else row["provider_family"]
        if row["series_type"] == "ensemble_mean":
            note = "集合平均；不可视为单一确定性模型"
        lines.append(
            f"| {row['job']} | `{row['model_id']}` | {row['series_type']} | "
            f"{history['http_status']}/{history['returned_hour_rows']}/{verdict(history)} | "
            f"{forecast['http_status']}/{forecast['returned_hour_rows']}/{verdict(forecast)} | {note} |"
        )
    total = len(rows)
    passed = sum(verdict(row["history"]) == "pass" and verdict(row["forecast"]) == "pass" for row in rows)
    lines += ["", f"**结果：{passed}/{total}项通过；其余项必须保留原始响应并标注`data_unavailable`。**"]
    Path(args.output).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
