import json
from collections import Counter

import pandas as pd


TXT_STRATEGIC = "三大先导"
TARGET_SALARY = 18000
TARGET_EMPLOYMENT_RATE = 90

INDUSTRY_SUGGESTIONS = {
    "常规行业": {
        "courses": ["行业应用专题", "数据分析与问题解决", "岗位能力综合训练"],
        "skills": ["项目执行能力", "数据处理能力", "岗位协同沟通能力"],
        "practice": ["企业案例工坊", "岗位情境模拟", "综合实践周"],
        "structure": "建议围绕行业通用能力重组课程模块，增强从基础课程到岗位应用的衔接。",
    },
    "人工智能": {
        "courses": ["机器学习基础", "深度学习应用", "数据工程与模型部署"],
        "skills": ["Python建模", "特征工程", "模型调优与评估"],
        "practice": ["算法项目实训", "企业数据集建模实验", "产业导师联合课题"],
        "structure": "建议将培养方向向人工智能应用与数据智能场景倾斜，提升算法课程占比与项目制学分。",
    },
    "集成电路": {
        "courses": ["数字电路设计", "嵌入式系统开发", "芯片测试与验证"],
        "skills": ["硬件调试", "Verilog/FPGA开发", "系统联调能力"],
        "practice": ["芯片设计实验", "硬件系统综合实训", "校企联合工程项目"],
        "structure": "建议强化硬件课程链路，增加从电路基础到系统实现的递进式训练。",
    },
    "生物医药": {
        "courses": ["药物研发基础", "生物统计与实验设计", "医药数据分析"],
        "skills": ["实验方案设计", "科研数据分析", "合规与质量控制"],
        "practice": ["医药研发实训", "实验室轮岗实践", "科研论文与专利训练"],
        "structure": "建议形成生物医药研发与数据分析双通道课程结构，增强科研转化能力。",
    },
    "现代金融": {
        "courses": ["金融数据分析", "量化投资基础", "商业分析与决策模型"],
        "skills": ["SQL与Python分析", "财务建模", "业务洞察表达"],
        "practice": ["量化分析实验", "金融案例工坊", "企业数据报告项目"],
        "structure": "建议在专业课中提高数据分析和金融科技相关模块占比，形成金融+数据复合培养路径。",
    },
    "教育科研": {
        "courses": ["教育数据分析", "课程设计与评估", "教育技术应用"],
        "skills": ["教学设计能力", "学习数据分析", "课堂组织与反馈能力"],
        "practice": ["课程工作坊", "教育场景实习", "教学反思项目"],
        "structure": "建议强化教学设计、教育技术和评价反馈三类课程模块，形成教学实践闭环。",
    },
    "文化传媒": {
        "courses": ["内容策划与数据分析", "数字传播工具", "品牌传播案例"],
        "skills": ["内容生产能力", "新媒体运营", "用户洞察与表达"],
        "practice": ["融媒体项目实训", "品牌传播案例工坊", "内容运营实践周"],
        "structure": "建议将传播理论课与数字内容生产课程打通，增强项目驱动型训练。",
    },
    "建筑工程": {
        "courses": ["工程项目管理", "BIM应用基础", "建筑信息化专题"],
        "skills": ["工程协同设计", "项目交付管理", "BIM建模与应用"],
        "practice": ["工程项目沙盘", "BIM综合实训", "校企联合施工案例"],
        "structure": "建议围绕工程设计、项目管理和数字建造三条主线重构课程链路。",
    },
    "智能制造": {
        "courses": ["智能制造系统", "工业数据采集与分析", "自动化控制基础"],
        "skills": ["工程仿真", "设备联调", "工业软件应用"],
        "practice": ["产线仿真实训", "智能工厂案例实践", "工程项目制课程"],
        "structure": "建议优化工程实践课程顺序，形成设计、仿真、实施一体化培养链路。",
    },
}

DISCIPLINE_SUGGESTIONS = {
    "工学": {
        "courses": ["工程系统设计", "行业应用专题"],
        "skills": ["工程实现能力", "跨团队协作能力"],
        "practice": ["综合工程训练", "企业真实需求项目"],
        "structure": "建议压缩重复理论课，增加工程设计与行业场景课程。",
    },
    "理学": {
        "courses": ["数据分析方法", "应用建模专题"],
        "skills": ["数理建模", "科研计算能力"],
        "practice": ["科研训练计划", "学科竞赛训练"],
        "structure": "建议增强理论到应用的转化课程，提升科研与产业结合度。",
    },
    "医学": {
        "courses": ["临床数据分析", "循证医学方法"],
        "skills": ["实验研究能力", "临床问题分析"],
        "practice": ["医院科研协同实践", "案例诊疗训练"],
        "structure": "建议构建科研训练与临床应用并重的课程模块。",
    },
    "管理学": {
        "courses": ["商业数据分析", "运营决策方法"],
        "skills": ["数据洞察", "项目统筹与沟通"],
        "practice": ["咨询案例实训", "企业经营模拟"],
        "structure": "建议提升数据驱动决策课程比重，减少纯理论重复内容。",
    },
    "经济学": {
        "courses": ["计量分析", "产业经济专题"],
        "skills": ["数据解释能力", "商业模型构建"],
        "practice": ["政策分析报告", "行业研究项目"],
        "structure": "建议增加量化分析与行业研究结合模块，强化就业适配度。",
    },
    "教育学": {
        "courses": ["课程设计方法", "教育评价与反馈"],
        "skills": ["教学设计能力", "学习支持与评估能力"],
        "practice": ["课堂观摩实习", "教学工作坊"],
        "structure": "建议围绕课程设计、教学实施和教育评价建立递进式培养结构。",
    },
    "文学": {
        "courses": ["内容策划", "传播分析与表达"],
        "skills": ["表达策划能力", "内容生产与传播能力"],
        "practice": ["内容创作项目", "传播案例实训"],
        "structure": "建议把表达训练、内容策划和数字传播课程整合为项目驱动式课程组。",
    },
    "艺术学": {
        "courses": ["创意策划与表达", "数字内容制作"],
        "skills": ["审美表达能力", "内容设计与呈现能力"],
        "practice": ["作品工作坊", "品牌内容项目实践"],
        "structure": "建议围绕创意表达、数字制作和项目展示构建模块化培养路径。",
    },
}

SKILL_LEVEL_SUGGESTIONS = {
    "初": {
        "courses": ["专业基础强化课", "工具链入门训练"],
        "skills": ["基础编码/分析能力", "专业工具熟练度"],
        "practice": ["基础实验周", "分层补强训练营"],
        "structure": "当前技能层级偏初级，建议先补齐底层能力，再进入高级方向课程。",
        "gap_score": 14,
    },
    "中": {
        "courses": ["进阶项目课", "综合案例分析"],
        "skills": ["问题拆解能力", "项目交付能力"],
        "practice": ["跨课程综合项目", "校企协同实践"],
        "structure": "当前技能层级已具备基础，建议通过项目制教学提升综合应用能力。",
        "gap_score": 8,
    },
    "高": {
        "courses": ["高级专题研讨", "前沿方向选修"],
        "skills": ["创新研究能力", "高阶问题解决能力"],
        "practice": ["科研课题实践", "高水平竞赛与成果孵化"],
        "structure": "当前技能基础较好，建议增加前沿专题和成果导向训练，形成优势培养方向。",
        "gap_score": 3,
    },
}


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def parse_rule_items(raw_text):
    text = str(raw_text or "").strip().strip("[]")
    if not text:
        return []
    return [item.strip().strip("'").strip('"') for item in text.split(",") if item.strip()]


def split_rule_dimensions(items):
    dimensions = {}
    for item in items:
        if ":" not in item:
            continue
        key, value = item.split(":", 1)
        dimensions[key.strip()] = value.strip()
    return dimensions


def pick_mode(series, default_value="-"):
    values = [str(value) for value in series if pd.notna(value) and str(value).strip()]
    if not values:
        return default_value
    return Counter(values).most_common(1)[0][0]


def unique_items(*groups, limit=3):
    merged = []
    for group in groups:
        for item in group:
            if item and item not in merged:
                merged.append(item)
    return merged[:limit]


def build_major_metrics(joined_pdf):
    grouped = (
        joined_pdf.groupby(["school_name", "school_level", "discipline_category", "major_name", "major_type"], dropna=False)
        .agg(
            employment_count=("student_id", "count"),
            avg_salary=("avg_salary", "mean"),
            strategic_ratio=("leading_industry_tag", lambda s: (s == TXT_STRATEGIC).mean()),
            high_skill_ratio=("skill_level", lambda s: (s == "高").mean()),
            dominant_industry=("industry_type", pick_mode),
            dominant_skill_level=("skill_level", pick_mode),
        )
        .reset_index()
    )

    grouped["avg_salary"] = grouped["avg_salary"].fillna(0).round(2)
    grouped["strategic_ratio"] = grouped["strategic_ratio"].fillna(0).round(4)
    grouped["high_skill_ratio"] = grouped["high_skill_ratio"].fillna(0).round(4)

    school_max = grouped.groupby("school_name")["employment_count"].transform("max").replace(0, 1)
    employment_share = grouped["employment_count"] / school_max
    salary_factor = grouped["avg_salary"] / TARGET_SALARY
    grouped["employment_rate_estimate"] = (
        74 + employment_share * 10 + grouped["strategic_ratio"] * 10 + grouped["high_skill_ratio"] * 4 + salary_factor * 4
    ).clip(70, 98).round(1)
    return grouped


def find_matching_rules(metric_row, rules_pdf):
    matched = []
    for rule in rules_pdf.to_dict("records"):
        antecedent_items = parse_rule_items(rule.get("antecedent"))
        dimensions = split_rule_dimensions(antecedent_items)

        match_count = 0
        if dimensions.get("专业") == metric_row["major_name"]:
            match_count += 3
        if dimensions.get("学科") == metric_row["discipline_category"]:
            match_count += 2
        if dimensions.get("专业类型") == metric_row["major_type"]:
            match_count += 2
        if dimensions.get("院校层次") == metric_row["school_level"]:
            match_count += 1
        if dimensions.get("行业") == metric_row["dominant_industry"]:
            match_count += 1
        if dimensions.get("技能") == metric_row["dominant_skill_level"]:
            match_count += 1

        if match_count == 0:
            continue

        rule_strength = (
            Number(rule.get("support")) * 100
            + Number(rule.get("confidence")) * 35
            + Number(rule.get("lift")) * 12
            + match_count * 6
        )
        enriched_rule = {
            **rule,
            "match_count": match_count,
            "rule_strength": round(rule_strength, 2),
            "dimensions": dimensions,
        }
        matched.append(enriched_rule)

    matched.sort(key=lambda item: (-item["rule_strength"], -Number(item.get("lift")), -Number(item.get("confidence"))))
    return matched[:3]


def Number(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def infer_action_type(priority_score, employment_rate_estimate, avg_salary):
    if priority_score >= 88:
        return "重点调优"
    if employment_rate_estimate >= 90 and avg_salary >= TARGET_SALARY:
        return "强化优势方向"
    if employment_rate_estimate < 84:
        return "补强就业导向"
    return "优化课程结构"


def build_single_suggestion(metric_row, matched_rules):
    industry_package = INDUSTRY_SUGGESTIONS.get(metric_row["dominant_industry"], INDUSTRY_SUGGESTIONS.get("常规行业"))
    discipline_package = DISCIPLINE_SUGGESTIONS.get(metric_row["discipline_category"], DISCIPLINE_SUGGESTIONS.get("工学"))
    skill_package = SKILL_LEVEL_SUGGESTIONS.get(metric_row["dominant_skill_level"], SKILL_LEVEL_SUGGESTIONS.get("中"))

    top_rule = matched_rules[0] if matched_rules else {
        "support": 0,
        "confidence": 0,
        "lift": 0,
        "rule_strength": 0,
        "antecedent": "[]",
        "consequent": "[]",
    }

    salary_gap_score = max(0, (TARGET_SALARY - Number(metric_row["avg_salary"])) / 1000 * 3.5)
    employment_gap_score = max(0, TARGET_EMPLOYMENT_RATE - Number(metric_row["employment_rate_estimate"])) * 0.8
    strategic_gap_score = max(0, 0.65 - Number(metric_row["strategic_ratio"])) * 40
    priority_score = round(
        Number(top_rule["rule_strength"]) * 0.55
        + salary_gap_score
        + employment_gap_score
        + strategic_gap_score
        + skill_package["gap_score"],
        2,
    )

    action_type = infer_action_type(priority_score, Number(metric_row["employment_rate_estimate"]), Number(metric_row["avg_salary"]))

    courses = unique_items(industry_package["courses"], discipline_package["courses"], skill_package["courses"])
    skills = unique_items(industry_package["skills"], discipline_package["skills"], skill_package["skills"])
    practice = unique_items(industry_package["practice"], discipline_package["practice"], skill_package["practice"])
    structure_parts = unique_items(
        [industry_package["structure"]],
        [discipline_package["structure"]],
        [skill_package["structure"]],
    )
    structure_text = " ".join(structure_parts)

    rule_evidence = [
        {
            "antecedent": item["antecedent"],
            "consequent": item["consequent"],
            "support": round(Number(item["support"]), 4),
            "confidence": round(Number(item["confidence"]), 4),
            "lift": round(Number(item["lift"]), 4),
        }
        for item in matched_rules
    ]

    evidence_summary = (
        f"匹配规则 {len(rule_evidence)} 条，最高提升度 {Number(top_rule['lift']):.2f}；"
        f"估算就业率 {Number(metric_row['employment_rate_estimate']):.1f}%；"
        f"平均薪资 {Number(metric_row['avg_salary']):.0f} 元；"
        f"主导行业 {metric_row['dominant_industry']}；主导技能层级 {metric_row['dominant_skill_level']}。"
    )
    explanation = (
        f"{metric_row['major_name']} 当前主要流向 {metric_row['dominant_industry']}，"
        f"且相关规则对接 {TXT_STRATEGIC} 的置信度为 {Number(top_rule['confidence']):.2f}、"
        f"提升度为 {Number(top_rule['lift']):.2f}。"
        f"结合该专业估算就业率 {Number(metric_row['employment_rate_estimate']):.1f}% 和平均薪资 "
        f"{Number(metric_row['avg_salary']):.0f} 元，建议优先执行 {action_type}。"
    )

    return {
        "school_name": metric_row["school_name"],
        "school_level": metric_row["school_level"],
        "discipline_category": metric_row["discipline_category"],
        "major_name": metric_row["major_name"],
        "major_type": metric_row["major_type"],
        "employment_count": int(metric_row["employment_count"]),
        "employment_rate_estimate": round(Number(metric_row["employment_rate_estimate"]), 1),
        "avg_salary": round(Number(metric_row["avg_salary"]), 2),
        "strategic_ratio": round(Number(metric_row["strategic_ratio"]), 4),
        "high_skill_ratio": round(Number(metric_row["high_skill_ratio"]), 4),
        "dominant_industry": metric_row["dominant_industry"],
        "dominant_skill_level": metric_row["dominant_skill_level"],
        "matched_rule_count": len(rule_evidence),
        "top_rule_support": round(Number(top_rule["support"]), 4),
        "top_rule_confidence": round(Number(top_rule["confidence"]), 4),
        "top_rule_lift": round(Number(top_rule["lift"]), 4),
        "priority_score": priority_score,
        "action_type": action_type,
        "recommended_courses": json.dumps(courses, ensure_ascii=False),
        "recommended_skills": json.dumps(skills, ensure_ascii=False),
        "recommended_practice": json.dumps(practice, ensure_ascii=False),
        "recommended_structure": structure_text,
        "rule_evidence": json.dumps(rule_evidence, ensure_ascii=False),
        "evidence_summary": evidence_summary,
        "explanation": explanation,
    }


def build_training_program_suggestions(joined_pdf, rules_pdf):
    if joined_pdf.empty:
        return pd.DataFrame()

    metrics_df = build_major_metrics(joined_pdf)
    suggestions = []
    for metric_row in metrics_df.to_dict("records"):
        matched_rules = find_matching_rules(metric_row, rules_pdf)
        suggestions.append(build_single_suggestion(metric_row, matched_rules))

    result_df = pd.DataFrame(suggestions)
    result_df = result_df.sort_values(
        by=["priority_score", "top_rule_lift", "employment_rate_estimate"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    return result_df
