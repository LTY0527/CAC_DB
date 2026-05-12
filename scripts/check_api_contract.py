from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "API_CONTRACT_CHECK_REPORT.md"
BASE_URL = "http://127.0.0.1:5000/api"


@dataclass
class ApiCase:
    role: str
    method: str
    path: str
    params: dict[str, Any] | None = None
    expected_fields: tuple[str, ...] = ()


ACCOUNTS = {
    "teacher": {"username": "teacher_shu", "password": "123456"},
    "government": {"username": "gov_sh", "password": "123456"},
    "public": {"username": "guest", "password": "123456"},
}

CASES = [
    ApiCase("teacher", "GET", "/demand/kpi", expected_fields=("high_demand_major_count", "avg_predicted_demand")),
    ApiCase("teacher", "GET", "/demand/forecast", expected_fields=("major_name", "predicted_demand_count")),
    ApiCase("teacher", "GET", "/enrollment/matching", {"major_code": "all", "limit": 10}, ("major_name", "match_score", "sample_count")),
    ApiCase("teacher", "GET", "/major/optimization", expected_fields=("items", "summary")),
    ApiCase("teacher", "GET", "/training/rules", expected_fields=("key", "evidence_score")),
    ApiCase("teacher", "GET", "/recommendation/summary", expected_fields=("covered_students", "available_examples")),
    ApiCase("teacher", "GET", "/recommendation/student", {"graduate_id": "__example__"}, ("items",)),
    ApiCase("teacher", "GET", "/report/ai", expected_fields=("report",)),
    ApiCase("teacher", "GET", "/employment-summary", expected_fields=("school_name", "major_name")),
    ApiCase("teacher", "GET", "/training-program-optimization", expected_fields=("major_name", "priority_score")),
    ApiCase("government", "GET", "/demand/kpi", expected_fields=("scope", "avg_predicted_demand")),
    ApiCase("government", "GET", "/demand/forecast", expected_fields=("major_name", "predicted_demand_count")),
    ApiCase("government", "GET", "/monitor/school", expected_fields=("items", "summary")),
    ApiCase("government", "GET", "/recommendation/summary", expected_fields=("covered_students", "available_examples")),
    ApiCase("public", "GET", "/monitor/school", expected_fields=("items", "summary")),
]


def request_json(method: str, path: str, token: str | None = None, params: dict[str, Any] | None = None, body: dict[str, Any] | None = None) -> dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(f"{BASE_URL}{path}{query}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return {"status": resp.status, "payload": json.loads(raw) if raw else None}


def safe_request(*args: Any, **kwargs: Any) -> dict[str, Any]:
    started = time.time()
    try:
        result = request_json(*args, **kwargs)
        result["elapsed_ms"] = round((time.time() - started) * 1000)
        return result
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw
        return {"status": exc.code, "payload": payload, "error": str(exc), "elapsed_ms": round((time.time() - started) * 1000)}
    except (URLError, TimeoutError, OSError) as exc:
        return {"status": None, "payload": None, "error": str(exc), "elapsed_ms": round((time.time() - started) * 1000)}


def flatten_data(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("items", "rows", "series", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [data]
    return []


def has_all_zero(rows: list[dict[str, Any]]) -> bool:
    numbers: list[float] = []
    for row in rows[:30]:
        for value in row.values():
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                numbers.append(float(value))
    return bool(numbers) and all(value == 0 for value in numbers)


def find_missing_fields(data: Any, fields: tuple[str, ...]) -> list[str]:
    if not fields:
        return []
    if isinstance(data, dict):
        top_level = set(data.keys())
        if all(field in top_level for field in fields):
            return []
    rows = flatten_data(data)
    if not rows:
        return list(fields)
    keys = set().union(*(row.keys() for row in rows[:5]))
    return [field for field in fields if field not in keys]


def login(role: str) -> tuple[str | None, dict[str, Any]]:
    result = safe_request("POST", "/auth/login", body=ACCOUNTS[role])
    payload = result.get("payload") or {}
    token = payload.get("data", {}).get("token") if isinstance(payload, dict) else None
    return token, result


def example_graduate_id(token: str, role: str) -> str | None:
    result = safe_request("GET", "/recommendation/summary", token=token)
    payload = result.get("payload") or {}
    data = payload.get("data") if isinstance(payload, dict) else {}
    examples = data.get("available_examples") if isinstance(data, dict) else []
    if examples:
        return str(examples[0])
    return None


def run_checks() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    tokens: dict[str, str] = {}
    for role in ACCOUNTS:
        token, result = login(role)
        tokens[role] = token or ""
        records.append({"scope": role, "path": "/auth/login", "result": result, "missing": [], "all_zero": False})

    for case in CASES:
        token = tokens.get(case.role)
        params = dict(case.params or {})
        if params.get("graduate_id") == "__example__":
            params["graduate_id"] = example_graduate_id(token, case.role) if token else ""
        result = safe_request(case.method, case.path, token=token, params=params)
        payload = result.get("payload") or {}
        data = payload.get("data") if isinstance(payload, dict) else None
        rows = flatten_data(data)
        records.append(
            {
                "scope": case.role,
                "path": case.path,
                "params": params,
                "result": result,
                "count": len(rows),
                "missing": find_missing_fields(data, case.expected_fields),
                "all_zero": has_all_zero(rows),
            }
        )
    return records


def ok_record(record: dict[str, Any]) -> bool:
    result = record.get("result", {})
    payload = result.get("payload")
    code = payload.get("code") if isinstance(payload, dict) else None
    return result.get("status") == 200 and code == 0 and not record.get("missing") and not record.get("all_zero")


def write_report(records: list[dict[str, Any]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# API_CONTRACT_CHECK_REPORT",
        "",
        "本报告由 `python scripts/check_api_contract.py` 生成，用于检查主要接口是否能按前端预期返回。",
        "",
        "| 状态 | 角色 | 接口 | 参数 | HTTP/code | 数据条数 | 字段缺失 | 全 0 风险 | 备注 |",
        "|---|---|---|---|---|---:|---|---|---|",
    ]
    for record in records:
        result = record.get("result", {})
        payload = result.get("payload")
        code = payload.get("code") if isinstance(payload, dict) else None
        status = "通过" if ok_record(record) else "关注"
        note = result.get("error") or (payload.get("message") if isinstance(payload, dict) else "")
        lines.append(
            f"| {status} | {record.get('scope','-')} | `{record.get('path')}` | `{record.get('params', {})}` | "
            f"{result.get('status')}/{code} | {record.get('count', 0)} | {', '.join(record.get('missing', [])) or '-'} | "
            f"{'是' if record.get('all_zero') else '否'} | {note or '-'} |"
        )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    records = run_checks()
    write_report(records)
    failed = [record for record in records if not ok_record(record)]
    print(f"API 合约巡检完成：{REPORT_PATH}，关注项 {len(failed)} 个。")


if __name__ == "__main__":
    main()
