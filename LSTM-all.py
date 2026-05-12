# -*- coding: utf-8 -*-
"""
兼容入口：旧版 LSTM-all.py 已升级为岗位需求人数预测入口。

请优先执行：
    python LSTM-job-demand.py

保留本文件是为了不破坏原有启动方式：
    python LSTM-all.py
"""

from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def load_job_demand_module():
    script_path = Path(__file__).resolve().parent / "LSTM-job-demand.py"
    spec = importlib.util.spec_from_file_location("lstm_job_demand", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载岗位需求预测脚本：{script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["lstm_job_demand"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    print("[LSTM-all] 兼容入口启动：当前已切换为“岗位需求人数预测”。")
    module = load_job_demand_module()
    return 0 if module.train_and_forecast() else 1


if __name__ == "__main__":
    sys.exit(main())
