from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"
REPORT_PATH = ROOT / "docs" / "FRONTEND_PAGE_CHECK_REPORT.md"


@dataclass
class Rule:
    name: str
    pattern: re.Pattern[str]
    risk: str
    suggestion: str


RULES = [
    Rule("mock/demo 数据残留", re.compile(r"\b(mock|fakeData|demoData)\b", re.I), "生产页面可能继续引用模拟数据。", "确认是否仅用于测试；生产页面应改为接口数据。"),
    Rule("fallbackData 残留", re.compile(r"\bfallbackData\b", re.I), "接口异常可能被静默兜底，掩盖真实错误。", "无数据时展示 Empty 状态并输出具体失败模块。"),
    Rule("图表数值强制补 0", re.compile(r"(\|\|\s*0|\?\?\s*0)"), "null/undefined 可能被转成 0，导致图表假低值或假全 0。", "图表缺失值优先保留 null，KPI 再做明确兜底。"),
    Rule("all 选择强制置 0", re.compile(r"(selectedMajor|currentMajor|major).*['\"]all['\"].{0,80}0", re.I), "全部专业状态可能被误判为空。", "全部专业应聚合当前范围 items，而不是默认 0。"),
    Rule("avg_sample_count 风险", re.compile(r"avg_sample_count|avgSampleCount"), "全部专业主 KPI 可能误用平均单专业样本量。", "全部专业主 KPI 应优先使用 total_sample_count 或 SUM(sample_count)。"),
    Rule("空图表渲染风险", re.compile(r"<ReactECharts[\s\S]{0,160}data", re.I), "图表可能在空数据时仍渲染坐标轴。", "渲染前判断 series/data 是否为空，空时显示 Empty。"),
    Rule("废弃 Top 筛选项", re.compile(r"Top\s*(5|15)|value:\s*(5|15)"), "页面仍可能暴露废弃 Top 5/Top 15 筛选。", "招生匹配页应固定 Top 10；其他页面如确有需要请标注。"),
    Rule("废弃候选筛选项", re.compile(r"全部候选"), "招生匹配页不应再显示候选阈值筛选。", "保留专业选择即可。"),
    Rule("旧薪资预测文案", re.compile(r"薪资预测"), "需求预测主目标可能仍被误写为薪资预测。", "改为岗位需求人数预测，薪资仅作辅助指标。"),
    Rule("笼统失败提示", re.compile(r"部分模块数据暂未返回|当前页面已使用可用数据继续渲染"), "接口失败时用户难以定位具体模块。", "提示中列出失败模块名，并在 console.warn 输出原因。"),
    Rule("字段名一致性风险", re.compile(r"matchScore|sampleCount|majorCode|predictedDemandCount|primarySuggestionType"), "camelCase 与后端 snake_case 混用可能导致读取为空。", "数据适配层统一兼容 snake_case/camelCase。"),
]


def iter_source_files() -> list[Path]:
    if not FRONTEND_SRC.exists():
        return []
    return [
        path
        for path in FRONTEND_SRC.rglob("*")
        if path.suffix in {".js", ".jsx", ".ts", ".tsx"} and path.is_file()
    ]


def scan() -> list[dict[str, str | int]]:
    findings: list[dict[str, str | int]] = []
    for path in iter_source_files():
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            for rule in RULES:
                if rule.pattern.search(line):
                    findings.append(
                        {
                            "rule": rule.name,
                            "file": str(path.relative_to(ROOT)),
                            "line": line_no,
                            "risk": rule.risk,
                            "suggestion": rule.suggestion,
                            "code": line.strip()[:180],
                        }
                    )
    return findings


def write_report(findings: list[dict[str, str | int]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# FRONTEND_PAGE_CHECK_REPORT",
        "",
        "本报告由 `python scripts/check_frontend_pages.py` 生成，采用静态扫描方式发现前端页面展示风险。",
        "",
        f"- 扫描目录：`{FRONTEND_SRC.relative_to(ROOT)}`",
        f"- 发现项：{len(findings)}",
        "",
    ]
    if not findings:
        lines.append("未发现规则命中的前端页面风险。")
    else:
        lines.extend(["| 规则 | 文件 | 行号 | 风险说明 | 建议修复 | 命中代码 |", "|---|---:|---:|---|---|---|"])
        for item in findings:
            code = str(item["code"]).replace("|", "\\|")
            lines.append(
                f"| {item['rule']} | `{item['file']}` | {item['line']} | {item['risk']} | {item['suggestion']} | `{code}` |"
            )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    findings = scan()
    write_report(findings)
    print(f"前端页面巡检完成：{REPORT_PATH}，发现 {len(findings)} 项。")


if __name__ == "__main__":
    main()
