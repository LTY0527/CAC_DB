# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data_seed.major_catalog_2025 import generate_major_catalog
from scripts.data_seed.school_profiles import SCHOOL_PROFILES
from scripts.industry_policy import leading_tag_for, random_enterprise_profile, synthetic_enterprise_name
from scripts.major_display_policy import is_valid_display_major_name

DATA_DIR = ROOT / "data" / "generated"
CONFIG_DIR = ROOT / "config"
MONTHS = pd.period_range("2024-01", "2026-12", freq="M").astype(str).tolist()

SCHOOL_SAMPLE_WEIGHTS = {
    "SHU001": 1.12,  # 上海交通大学
    "SHU002": 1.08,  # 复旦大学
    "SHU003": 1.07,  # 同济大学
    "SHU004": 0.98,  # 华东师范大学
    "SHU005": 0.98,  # 华东理工大学
    "SHU006": 0.90,  # 上海财经大学
    "SHU007": 1.18,  # 上海大学
    "SHU008": 0.90,  # 东华大学
    "SHU009": 0.82,  # 上海外国语大学
    "SHU010": 0.97,  # 上海理工大学
}

EMPLOYMENT_SAMPLE_WEIGHTS = {
    "SHU001": 1.18,
    "SHU002": 1.12,
    "SHU003": 1.08,
    "SHU004": 0.96,
    "SHU005": 1.00,
    "SHU006": 0.86,
    "SHU007": 1.16,
    "SHU008": 0.88,
    "SHU009": 0.78,
    "SHU010": 0.98,
}

POLICY_GROWTH = {
    "人工智能": 1.36,
    "数据要素": 1.28,
    "集成电路": 1.32,
    "新能源": 1.28,
    "智能制造": 1.25,
    "金融科技": 1.18,
    "护理康养": 1.22,
    "绿色低碳": 1.18,
    "数字文化": 1.18,
    "低空经济": 1.30,
}

MAJOR_JOB_AFFINITY = {
    "临床医学": ["临床医生", "药物研发", "公共卫生专员"],
    "护理学": ["护理师", "康养服务专员"],
    "药学": ["药物研发", "制药工程师"],
    "医学影像技术": ["医学影像技师"],
    "金融学": ["金融分析师", "风险控制", "投资研究"],
    "国际经济与贸易": ["国际商务", "跨境电商运营", "供应链管理"],
    "会计学": ["会计审计", "税务顾问"],
    "财务管理": ["会计审计", "风险控制"],
    "机械设计制造及其自动化": ["机械工程师", "自动化工程师", "质量工程师"],
    "机械工程": ["机械工程师", "机器人工程师"],
    "新能源科学与工程": ["能源工程师", "储能工程师", "新能源汽车工程师"],
    "能源与动力工程": ["能源工程师", "动力系统工程师"],
    "环境工程": ["环境工程师", "碳管理专员", "水处理工程师"],
    "建筑学": ["建筑设计师", "城市规划师"],
    "城乡规划": ["城市规划师", "交通规划师"],
    "土木工程": ["土木工程师", "结构工程师", "BIM工程师"],
    "英语": ["翻译", "本地化专员", "国际商务"],
    "翻译": ["翻译", "本地化专员", "国际传播"],
    "数字媒体技术": ["数字媒体设计", "内容策划", "新媒体运营"],
    "广播电视学": ["新闻编辑", "内容策划", "影视编导"],
    "数据科学与大数据技术": ["数据分析师", "数据开发工程师", "算法工程师"],
    "软件工程": ["后端开发", "前端开发", "软件测试"],
    "计算机科学与技术": ["后端开发", "算法工程师", "数据库开发"],
    "通信工程": ["通信工程师", "物联网工程师", "网络工程师"],
    "电子信息工程": ["电子信息工程师", "通信工程师"],
    "集成电路设计与集成系统": ["芯片验证工程师", "射频工程师"],
    "化学工程与工艺": ["化工工艺工程师", "工艺工程师"],
    "制药工程": ["制药工程师", "药物研发"],
    "高分子材料与工程": ["材料工程师", "高分子工程师"],
    "金属材料工程": ["材料工程师", "质量工程师"],
    "纺织工程": ["纺织工程师", "面料研发"],
    "服装设计与工程": ["服装设计师", "品牌运营"],
    "社会学": ["社会工作者", "公共事务专员"],
    "档案学": ["档案管理", "信息资源管理"],
    "汉语言文学": ["教师", "内容策划", "新闻编辑"],
    "教育学": ["教师", "课程研发"],
    "心理学": ["心理咨询师", "教育技术专员"],
}

BLOCKED_COMBOS = {
    ("临床医学", "设施农业工程师"),
    ("国际经济与贸易", "电池研发工程师"),
    ("数学与应用数学", "新能源汽车工程师"),
    ("护理学", "前端开发"),
    ("英语", "新能源汽车工程师"),
    ("翻译", "新能源汽车工程师"),
    ("建筑学", "护理师"),
}


def weighted_choice(rng: random.Random, items, weights):
    return rng.choices(items, weights=[max(float(w), 0.001) for w in weights], k=1)[0]


def allocate_counts(total: int, keys: list[str], weights_by_key: dict[str, float]) -> dict[str, int]:
    weights = {key: float(weights_by_key.get(key, 1.0)) for key in keys}
    weight_sum = sum(weights.values()) or 1.0
    raw = {key: total * weights[key] / weight_sum for key in keys}
    counts = {key: int(raw[key]) for key in keys}
    remain = total - sum(counts.values())
    for key in sorted(keys, key=lambda item: raw[item] - counts[item], reverse=True)[:remain]:
        counts[key] += 1
    return counts


def month_factor(month: str) -> float:
    m = int(month[-2:])
    if m in (9, 10, 11):
        return {9: 1.34, 10: 1.45, 11: 1.30}[m]
    if m in (3, 4, 5):
        return {3: 1.18, 4: 1.26, 5: 1.14}[m]
    if m in (1, 2):
        return 0.78
    if m in (7, 8):
        return 0.86
    return 1.0


def stable_ratio(*parts) -> float:
    key = "|".join(str(part) for part in parts)
    return (sum((idx + 1) * ord(ch) for idx, ch in enumerate(key)) % 1000) / 1000


def parse_yaml_value(raw: str):
    value = raw.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.startswith("[") and value.endswith("]"):
        inside = value[1:-1].strip()
        return [parse_yaml_value(part) for part in inside.split(",") if part.strip()]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("'\"")


def parse_job_taxonomy(path: Path) -> dict:
    groups: list[dict] = []
    current_group: dict | None = None
    current_job: dict | None = None
    in_categories = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped == "groups:":
            continue
        if line.startswith("  - group_name:") or line.startswith("  - name:"):
            key, raw_value = stripped[2:].split(":", 1)
            current_group = {"group_name": parse_yaml_value(raw_value), "categories": []}
            current_group[key.strip()] = parse_yaml_value(raw_value)
            groups.append(current_group)
            current_job = None
            in_categories = False
            continue
        if current_group is None:
            continue
        if stripped == "categories:":
            in_categories = True
            current_job = None
            continue
        if in_categories and line.startswith("    - job_category_name:"):
            current_job = {"job_category_name": parse_yaml_value(stripped.split(":", 1)[1])}
            current_group["categories"].append(current_job)
            continue
        if ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        if in_categories and current_job is not None:
            current_job[key] = parse_yaml_value(raw_value)
        else:
            current_group[key] = parse_yaml_value(raw_value)
    return {"groups": groups}


def load_job_taxonomy() -> tuple[pd.DataFrame, pd.DataFrame]:
    data = parse_job_taxonomy(CONFIG_DIR / "job_taxonomy.yaml")
    industries = []
    jobs = []
    job_id = 1
    for industry_id, group in enumerate(data["groups"], start=1):
        tags = "、".join(group.get("policy_direction_tags", []))
        growth = {"high": 1.16, "medium": 1.07, "low": 0.98}.get(group.get("demand_growth_level"), 1.04)
        industries.append({
            "industry_id": industry_id,
            "industry_name": group["name"],
            "is_shanghai_leading_industry": 0,
            "leading_industry_name": "",
            "leading_industry_code": "",
            "policy_direction_tags": tags,
            "base_growth_factor": growth,
        })
        for job_name in group["jobs"]:
            low, high = group["salary_band"]
            jobs.append({
                "job_category_id": job_id,
                "job_category_name": job_name,
                "industry_id": industry_id,
                "job_group": group["name"],
                "computer_related": int(bool(group.get("computer_related"))),
                "skill_tags": "、".join(group["skills"]),
                "compatible_major_classes": "、".join(group["majors"]),
                "salary_min_base": low,
                "salary_max_base": high,
                "demand_growth_level": group["demand_growth_level"],
                "policy_direction_tags": tags,
            })
            job_id += 1
    industries_df = pd.DataFrame(industries)
    for idx, row in industries_df.iterrows():
        is_leading, leading_name, leading_code = leading_tag_for(
            row["industry_id"],
            row["industry_name"],
            row.get("policy_direction_tags", ""),
        )
        industries_df.loc[idx, "is_shanghai_leading_industry"] = is_leading
        industries_df.loc[idx, "leading_industry_name"] = leading_name
        industries_df.loc[idx, "leading_industry_code"] = leading_code
    return industries_df, pd.DataFrame(jobs)


def build_schools() -> pd.DataFrame:
    rows = []
    for item in SCHOOL_PROFILES:
        row = {k: v for k, v in item.items() if k != "ace_majors"}
        row["discipline_strength_tags"] = "、".join(item["discipline_strength_tags"])
        row["industry_affinity"] = "、".join(item["industry_affinity"])
        rows.append(row)
    return pd.DataFrame(rows)


def build_school_major(catalog: pd.DataFrame, rng: random.Random) -> pd.DataFrame:
    by_name = catalog.set_index("major_name").to_dict("index")
    rows = []
    for school in SCHOOL_PROFILES:
        selected = []
        for major_name in school["ace_majors"]:
            if major_name in by_name:
                selected.append(by_name[major_name]["major_code"])
        display_catalog = catalog[
            (catalog["is_real_display_major"].astype(int) == 1)
            & (catalog["is_catalog_placeholder"].astype(int) == 0)
            & (~catalog["major_name"].astype(str).str.contains(r"\d+$", regex=True))
        ].copy()
        records = display_catalog.to_dict("records")
        weights = []
        for major in records:
            text = f"{major['major_name']} {major['major_class']} {major['policy_direction_tags']}"
            hit = any(tag in text for tag in school["discipline_strength_tags"])
            affinity = any(tag in text for tag in school["industry_affinity"])
            priority = float(major.get("display_priority", 0) or 0) / 100
            weights.append((6 if hit else (3 if affinity else 1)) + priority)
        while len(set(selected)) < school["major_count"]:
            selected.append(weighted_choice(rng, [r["major_code"] for r in records], weights))
        selected = list(dict.fromkeys(selected))[: school["major_count"]]
        first_class_left = school["first_class_major_count"]
        for code in selected:
            major = catalog.loc[catalog["major_code"] == code].iloc[0]
            is_ace = int(major["major_name"] in school["ace_majors"])
            strength = min(100, rng.uniform(62, 82) + is_ace * rng.uniform(10, 16) + school["research_factor"] * 3)
            scale = rng.uniform(50, 150) * school["application_factor"]
            if school["school_id"] == "SHU007":
                scale *= 1.22
            rows.append({
                "school_id": school["school_id"],
                "major_code": code,
                "is_enrolling": 1,
                "is_ace_major": is_ace,
                "is_first_class_major": int(is_ace or first_class_left > 0),
                "school_major_strength_score": round(strength, 2),
                "historical_enrollment_scale": int(scale),
                "major_status": "优势专业" if is_ace else "正常招生",
            })
            if first_class_left > 0:
                first_class_left -= 1
    return pd.DataFrame(rows)


def build_enterprises(industries: pd.DataFrame, rng: random.Random, n=3500) -> pd.DataFrame:
    districts = ["浦东新区", "徐汇区", "杨浦区", "闵行区", "宝山区", "长宁区", "静安区", "黄浦区", "嘉定区", "松江区"]
    scales = [("小微企业", 0.90, 0.88), ("中型企业", 1.00, 1.00), ("大型企业", 1.16, 1.12), ("头部企业", 1.34, 1.22)]
    rows = []
    industry_records = industries.to_dict("records")
    leading_industry_records = [item for item in industry_records if int(item.get("is_shanghai_leading_industry", 0)) == 1]
    for enterprise_id in range(1, n + 1):
        industry = rng.choice(leading_industry_records) if leading_industry_records and rng.random() < 0.34 else rng.choice(industry_records)
        scale, salary_factor, stability = weighted_choice(rng, scales, [38, 34, 20, 8])
        district = rng.choice(districts)
        is_leading, leading_name, leading_code = leading_tag_for(
            industry["industry_id"],
            industry.get("industry_name", ""),
            industry.get("policy_direction_tags", ""),
        )
        profile = random_enterprise_profile(rng, district, is_leading)
        rows.append({
            "enterprise_id": enterprise_id,
            "enterprise_name": synthetic_enterprise_name(industry["industry_name"], leading_code, enterprise_id),
            "industry_id": industry["industry_id"],
            "city": "上海市",
            "district": district,
            "enterprise_scale": scale,
            "ownership_type": weighted_choice(rng, ["国有", "民营", "外资", "合资", "事业单位", "科研院所"], [18, 48, 12, 10, 8, 4]),
            "is_high_tech": int(industry["base_growth_factor"] >= 1.12 or is_leading or rng.random() < 0.22),
            "is_specialized_new": int(rng.random() < (0.34 if is_leading else 0.20)),
            "is_shanghai_leading_enterprise": is_leading,
            "leading_industry_name": leading_name,
            "leading_industry_code": leading_code,
            **profile,
            "salary_factor": round(salary_factor * rng.uniform(0.92, 1.10), 3),
            "hiring_stability_factor": round(stability * rng.uniform(0.9, 1.10), 3),
        })
    return pd.DataFrame(rows)


def job_affinity(major: dict, job: dict) -> float:
    major_name = major["major_name"]
    job_name = job["job_category_name"]
    if (major_name, job_name) in BLOCKED_COMBOS:
        return 0.0
    score = 0.25
    if major["major_class"] in str(job["compatible_major_classes"]):
        score += 4.0
    if job_name in MAJOR_JOB_AFFINITY.get(major_name, []):
        score += 8.0
    if any(tag and tag in str(job["policy_direction_tags"]) for tag in str(major["policy_direction_tags"]).split("、")):
        score += 1.2
    if job["job_category_name"] == "设施农业工程师" and major_name not in {"智能植物生产学1", "现代农业工程工程1"}:
        score *= 0.08
    return score


def scale_demand_range(scale: str, high_tech: int, growth: str) -> tuple[int, int]:
    if scale == "小微企业":
        low, high = 1, 5
    elif scale == "中型企业":
        low, high = 3, 20
    elif scale == "大型企业":
        low, high = 10, 80
    else:
        low, high = 30, 150
    if high_tech and growth == "high":
        high = int(high * 1.35)
        low = int(low * 1.2)
    return max(1, low), max(low + 1, high)


def build_postings(enterprises, jobs, bridge, catalog, schools, rng, n=80000) -> pd.DataFrame:
    rows = []
    major_map = catalog.set_index("major_code").to_dict("index")
    school_map = schools.set_index("school_id").to_dict("index")
    bridge_records = bridge.to_dict("records")
    bridge_weights = [r["historical_enrollment_scale"] * (1.45 if r["school_id"] == "SHU007" else 1.0) for r in bridge_records]
    enterprise_records = enterprises.to_dict("records")
    enterprise_by_industry = defaultdict(list)
    for enterprise in enterprise_records:
        enterprise_by_industry[enterprise["industry_id"]].append(enterprise)
    job_records = jobs.to_dict("records")
    job_by_id = jobs.set_index("job_category_id").to_dict("index")
    for posting_id in range(1, n + 1):
        bm = weighted_choice(rng, bridge_records, bridge_weights)
        major = major_map[bm["major_code"]]
        weights = [job_affinity(major, job) for job in job_records]
        job = weighted_choice(rng, job_records, weights)
        enterprise_pool = enterprise_by_industry.get(job["industry_id"]) or enterprise_records
        ent = rng.choice(enterprise_pool)
        month = rng.choice(MONTHS)
        low, high = scale_demand_range(ent["enterprise_scale"], ent["is_high_tech"], job["demand_growth_level"])
        policy = max([POLICY_GROWTH.get(tag, 1.0) for tag in str(job["policy_direction_tags"]).split("、") if tag] or [1.0])
        strength = 1 + (bm["school_major_strength_score"] - 70) / 180 + bm["is_ace_major"] * 0.22
        affinity = job_affinity(major, job)
        match_factor = 0.72 + min(affinity, 12.0) / 12.0 * 0.55
        combo_seed = stable_ratio(bm["school_id"], bm["major_code"], job["job_category_id"])
        base_factor = 0.82 + combo_seed * 0.46
        trend_factor = 1.0 + (combo_seed - 0.5) * 0.16
        industry_cycle = 0.90 + stable_ratio(job["industry_id"], month[-2:]) * 0.22
        noise = rng.uniform(0.88, 1.14)
        demand_count = int(
            rng.triangular(low, high, (low + high) / 2)
            * month_factor(month)
            * policy
            * max(0.7, strength)
            * match_factor
            * base_factor
            * trend_factor
            * industry_cycle
            * noise
        )
        demand_count = max(1, demand_count)
        school = school_map[bm["school_id"]]
        salary_min = int(job["salary_min_base"] * ent["salary_factor"] * school["salary_level_factor"] * rng.uniform(0.9, 1.08))
        salary_max = int(job["salary_max_base"] * ent["salary_factor"] * school["salary_level_factor"] * rng.uniform(0.95, 1.15))
        rows.append({
            "posting_id": posting_id,
            "enterprise_id": ent["enterprise_id"],
            "industry_id": ent["industry_id"],
            "job_category_id": job["job_category_id"],
            "month": month,
            "city": "上海市",
            "demand_count": demand_count,
            "salary_min": salary_min,
            "salary_max": max(salary_max, salary_min + 1800),
            "education_required": weighted_choice(rng, ["本科", "硕士", "博士"], [70, 25, 5]),
            "experience_level": weighted_choice(rng, ["应届", "1-3年", "3-5年"], [60, 30, 10]),
            "skill_tags": job_by_id[job["job_category_id"]]["skill_tags"],
            "preferred_major_codes": bm["major_code"],
            "policy_direction_tags": job["policy_direction_tags"],
            "school_preference_level": round(min(100, bm["school_major_strength_score"] * school["research_factor"] / 1.08), 2),
            "is_shanghai_leading_job": int(ent.get("is_shanghai_leading_enterprise", 0)),
            "leading_industry_name": ent.get("leading_industry_name", ""),
            "leading_industry_code": ent.get("leading_industry_code", ""),
            "job_title": job["job_category_name"],
            "job_category": job["job_category_name"],
            "contract_type": weighted_choice(rng, ["劳动合同", "校招协议", "实习转正", "项目合同"], [72, 18, 7, 3]),
        })
    return pd.DataFrame(rows)


def build_graduates(bridge, rng, n=52000) -> pd.DataFrame:
    rows = []
    records = bridge.to_dict("records")
    records_by_school = defaultdict(list)
    for record in records:
        records_by_school[record["school_id"]].append(record)
    school_ids = sorted(records_by_school)
    school_counts = allocate_counts(n, school_ids, SCHOOL_SAMPLE_WEIGHTS)
    graduate_id = 1
    skills = ["Python", "SQL", "项目实践", "数据分析", "沟通协作", "行业研究", "英语", "Office", "实验规范", "工程制图", "风险管理"]
    for school_id in school_ids:
        school_records = records_by_school[school_id]
        weights = [r["historical_enrollment_scale"] for r in school_records]
        for _ in range(school_counts[school_id]):
            bm = weighted_choice(rng, school_records, weights)
            rows.append({
                "graduate_id": graduate_id,
                "school_id": bm["school_id"],
                "major_code": bm["major_code"],
                "graduation_year": weighted_choice(rng, [2024, 2025, 2026], [32, 34, 34]),
                "gender": weighted_choice(rng, ["男", "女"], [49, 51]),
                "degree_level": weighted_choice(rng, ["本科", "硕士"], [82, 18]),
                "gpa_level": weighted_choice(rng, ["A", "B", "C"], [26, 52, 22]),
                "skill_tags": "、".join(rng.sample(skills, rng.randint(3, 5))),
                "internship_count": weighted_choice(rng, [0, 1, 2, 3], [10, 40, 36, 14]),
                "certification_tags": "、".join(rng.sample(["四六级", "职业资格", "竞赛获奖", "项目证书", "无"], 2)),
                "job_intention_tags": weighted_choice(rng, ["上海就业", "长三角", "升学深造", "基层服务", "创业"], [62, 18, 10, 7, 3]),
            })
            graduate_id += 1
    return pd.DataFrame(rows)


def build_employment(graduates, postings, enterprises, jobs, bridge, schools, rng, n=42000) -> pd.DataFrame:
    rows = []
    post_by_major = defaultdict(list)
    for row in postings.to_dict("records"):
        post_by_major[row["preferred_major_codes"]].append(row)
    ent_map = enterprises.set_index("enterprise_id").to_dict("index")
    school_map = schools.set_index("school_id").to_dict("index")
    bridge_map = {(r.school_id, r.major_code): r for r in bridge.itertuples()}
    grad_by_school = defaultdict(list)
    for record in graduates.to_dict("records"):
        grad_by_school[record["school_id"]].append(record)
    school_ids = sorted(grad_by_school)
    target_counts = allocate_counts(min(n, len(graduates)), school_ids, EMPLOYMENT_SAMPLE_WEIGHTS)
    selected_graduates = []
    for school_id in school_ids:
        records = grad_by_school[school_id]
        rng.shuffle(records)
        selected_graduates.extend(records[: min(target_counts[school_id], len(records))])
    rng.shuffle(selected_graduates)
    employment_id = 1
    for grad in selected_graduates:
        candidates = post_by_major.get(grad["major_code"]) or postings.sample(30, random_state=rng.randint(1, 999999)).to_dict("records")
        post = rng.choice(candidates)
        ent = ent_map[post["enterprise_id"]]
        bm = bridge_map.get((grad["school_id"], grad["major_code"]))
        school = school_map[grad["school_id"]]
        quality = 0.58 + (float(bm.school_major_strength_score) if bm else 70) / 250 + school["employment_stability_factor"] * 0.08
        quality += {"A": 0.05, "B": 0.0, "C": -0.04}[grad["gpa_level"]]
        quality += min(0.08, grad["internship_count"] * 0.025)
        quality = max(0.42, min(0.96, quality + rng.uniform(-0.08, 0.07)))
        salary = int(rng.uniform(post["salary_min"], post["salary_max"]) * (0.82 + quality * 0.28))
        social_security_verified = int(rng.random() < 0.91)
        employment_month = rng.choice([m for m in MONTHS if m.startswith(str(grad["graduation_year"]))] or MONTHS[-12:])
        rows.append({
            "employment_id": employment_id,
            "graduate_id": grad["graduate_id"],
            "school_id": grad["school_id"],
            "major_code": grad["major_code"],
            "enterprise_id": post["enterprise_id"],
            "industry_id": post["industry_id"],
            "job_category_id": post["job_category_id"],
            "employment_month": employment_month,
            "salary": salary,
            "employment_type": weighted_choice(rng, ["签约就业", "灵活就业", "升学后就业", "基层项目"], [78, 10, 8, 4]),
            "city": "上海市",
            "match_score": round(quality * 100, 2),
            "is_major_related": int(rng.random() < 0.88),
            "social_security_verified": social_security_verified,
            "employment_quality_level": "高" if quality >= 0.82 else ("中" if quality >= 0.66 else "低"),
            "is_shanghai_leading_employment": int(ent.get("is_shanghai_leading_enterprise", 0)),
            "leading_industry_name": ent.get("leading_industry_name", ""),
            "leading_industry_code": ent.get("leading_industry_code", ""),
            "social_security_status": "在沪参保" if social_security_verified else "未核验",
            "first_shanghai_insurance_month": employment_month if social_security_verified else "",
        })
        employment_id += 1
        if employment_id > n:
            break
    return pd.DataFrame(rows)


def build_enrollment_plan(bridge, catalog, schools, rng) -> pd.DataFrame:
    rows = []
    plan_id = 1
    school_map = schools.set_index("school_id").to_dict("index")
    for year in range(2012, 2029):
        for bm in bridge.to_dict("records"):
            school = school_map[bm["school_id"]]
            heat = 1 + bm["is_ace_major"] * 0.25 + bm["school_major_strength_score"] / 500 + school["policy_response_factor"] / 12
            quota = max(20, int(bm["historical_enrollment_scale"] * rng.uniform(0.80, 1.18)))
            rows.append({
                "plan_id": plan_id,
                "school_id": bm["school_id"],
                "major_code": bm["major_code"],
                "year": year,
                "planned_quota": quota,
                "actual_enrollment": max(1, int(quota * rng.uniform(0.92, 1.06))),
                "applicant_count": int(quota * rng.uniform(2.8, 8.8) * heat),
                "first_choice_rate": round(min(0.96, rng.uniform(0.38, 0.82) * heat), 4),
                "admission_score_avg": int(520 + school["research_factor"] * 34 + bm["school_major_strength_score"] * 0.8 + rng.uniform(-18, 18)),
                "enrollment_satisfaction_score": round(min(100, 62 + heat * 16 + rng.uniform(-6, 6)), 2),
            })
            plan_id += 1
    return pd.DataFrame(rows)


def build_course_skill(bridge, catalog, rng) -> pd.DataFrame:
    rows = []
    cid = 1
    major_map = catalog.set_index("major_code").to_dict("index")
    for bm in bridge.to_dict("records"):
        major = major_map[bm["major_code"]]
        tokens = [major["major_name"], major["major_class"].replace("类", ""), "行业实践", "数据素养", "项目实训", "职业伦理"]
        for k in range(17):
            rows.append({
                "course_id": cid,
                "school_id": bm["school_id"],
                "major_code": bm["major_code"],
                "course_name": f"{tokens[k % len(tokens)]}{['基础', '方法', '综合实验', '案例分析'][k % 4]}",
                "skill_tags": "、".join(rng.sample(tokens + ["Python", "SQL", "调研分析", "工程制图", "跨文化沟通", "质量管理"], 4)),
                "course_type": weighted_choice(rng, ["专业核心", "实践实训", "通识拓展", "校企合作"], [42, 26, 18, 14]),
                "practice_hours": int(rng.uniform(16, 108) * (1.15 if bm["is_ace_major"] else 1.0)),
                "industry_alignment_score": round(min(100, rng.uniform(60, 84) + bm["is_ace_major"] * 9 + bm["school_major_strength_score"] / 12), 2),
            })
            cid += 1
    return pd.DataFrame(rows)


def build_policy_signal(catalog, industries, rng, n=5000) -> pd.DataFrame:
    rows = []
    directions = list(POLICY_GROWTH)
    display_catalog = catalog[
        (catalog["is_real_display_major"].astype(int) == 1)
        & (catalog["is_catalog_placeholder"].astype(int) == 0)
        & (catalog["major_name"].astype(str).map(is_valid_display_major_name))
    ]
    if display_catalog.empty:
        display_catalog = catalog
    for policy_id in range(1, n + 1):
        direction = weighted_choice(rng, directions, [POLICY_GROWTH[d] for d in directions])
        industry = industries.sample(1, random_state=rng.randint(1, 999999)).iloc[0]
        major = display_catalog.sample(1, random_state=rng.randint(1, 999999)).iloc[0]
        month = rng.choice(MONTHS)
        rows.append({
            "policy_id": policy_id,
            "month": month,
            "policy_direction": direction,
            "industry_id": int(industry.industry_id),
            "major_code": major.major_code,
            "policy_heat": round(min(100, rng.uniform(42, 74) * POLICY_GROWTH[direction]), 2),
            "city_support_score": round(rng.uniform(58, 96), 2),
            "strategy_level": weighted_choice(rng, ["国家级", "市级", "区级", "行业级"], [18, 40, 28, 14]),
            "description": f"{month} 上海围绕{direction}推动{industry.industry_name}与{major.major_name}人才协同。",
        })
    return pd.DataFrame(rows)


def write_reports(tables: dict[str, pd.DataFrame]) -> None:
    posting_month = tables["fact_job_posting"].groupby("month")["demand_count"].sum()
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "table_rows": {name: int(len(df)) for name, df in tables.items()},
        "shanghai_university": {
            "bridge_major_count": int((tables["bridge_school_major"]["school_id"] == "SHU007").sum()),
            "graduate_count": int((tables["fact_graduate"]["school_id"] == "SHU007").sum()),
            "employment_count": int((tables["fact_employment"]["school_id"] == "SHU007").sum()),
        },
        "major_catalog_count": int(len(tables["dim_major_catalog"])),
        "discipline_count": int(tables["dim_major_catalog"]["discipline_category"].nunique()),
        "major_class_count": int(tables["dim_major_catalog"]["major_class"].nunique()),
        "computer_job_ratio": round(float(tables["dim_job_category"]["computer_related"].mean()), 4),
        "seasonality_ratio": round(float(posting_month.max() / max(posting_month.min(), 1)), 3),
        "monthly_demand_min": int(posting_month.min()),
        "monthly_demand_max": int(posting_month.max()),
    }
    (DATA_DIR / "data_quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# DATA QUALITY REPORT", "", "| 指标 | 值 |", "| --- | --- |"]
    for key, value in report.items():
        lines.append(f"| {key} | {value} |")
    (DATA_DIR / "data_quality_report.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "DATA_GENERATION_REPORT.md").write_text(
        "# DATA_GENERATION_REPORT\n\n"
        f"- 总行数：{sum(report['table_rows'].values())}\n"
        f"- 上海大学毕业生：{report['shanghai_university']['graduate_count']}\n"
        f"- 上海大学就业记录：{report['shanghai_university']['employment_count']}\n"
        f"- 上海大学开设专业：{report['shanghai_university']['bridge_major_count']}\n"
        f"- 岗位需求季节峰谷比：{report['seasonality_ratio']}\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=150000)
    parser.add_argument("--seed", type=int, default=20260427)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    catalog = pd.DataFrame(generate_major_catalog())
    industries, jobs = load_job_taxonomy()
    schools = build_schools()
    bridge = build_school_major(catalog, rng)
    enterprises = build_enterprises(industries, rng, n=max(5000, int(args.rows * 0.018)))
    postings = build_postings(enterprises, jobs, bridge, catalog, schools, rng, n=max(120000, int(args.rows * 0.42)))
    graduates = build_graduates(bridge, rng, n=max(120000, int(args.rows * 0.40)))
    employment = build_employment(graduates, postings, enterprises, jobs, bridge, schools, rng, n=max(100000, int(args.rows * 0.34)))
    enrollment = build_enrollment_plan(bridge, catalog, schools, rng)
    course_skill = build_course_skill(bridge, catalog, rng)
    policy = build_policy_signal(catalog, industries, rng, n=max(4000, int(args.rows * 0.034)))

    tables = {
        "dim_school": schools,
        "dim_major_catalog": catalog,
        "bridge_school_major": bridge,
        "dim_industry": industries,
        "dim_job_category": jobs,
        "dim_enterprise": enterprises,
        "fact_job_posting": postings,
        "fact_graduate": graduates,
        "fact_employment": employment,
        "fact_enrollment_plan": enrollment,
        "fact_course_skill": course_skill,
        "fact_policy_signal": policy,
    }
    for name, df in tables.items():
        df.to_csv(DATA_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    write_reports(tables)
    print(json.dumps({name: len(df) for name, df in tables.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
