# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parents[1]

LEADING_INDUSTRIES = {
    "AI": {
        "name": "人工智能",
        "industry_ids": {2},
        "keywords": {
            "人工智能", "算法", "机器学习", "深度学习", "大模型", "智能机器人",
            "计算机视觉", "自然语言处理",
            # Mojibake aliases retained because several seed files are stored with garbled Chinese text.
            "浜哄伐鏅鸿兘", "绠楁硶", "鏈哄櫒瀛︿範", "娣卞害瀛︿範", "鏅鸿兘",
        },
    },
    "IC": {
        "name": "集成电路",
        "industry_ids": {3},
        "keywords": {
            "集成电路", "芯片", "半导体", "IC设计", "IC验证", "晶圆制造", "封装测试",
            "闆嗘垚鐢佃矾", "鑺墖", "鍗婂浣", "IC", "鐢佃矾",
        },
    },
    "BIOMED": {
        "name": "生物医药",
        "industry_ids": {6, 7},
        "keywords": {
            "生物医药", "医药研发", "药物研发", "生物技术", "医疗器械", "临床研究", "制药",
            "鐢熺墿鍖昏嵂", "鑽墿", "鍒惰嵂", "鍖荤枟", "鍋ュ悍", "涓村簥",
        },
    },
}

LEADING_CODES = tuple(LEADING_INDUSTRIES)


def leading_tag_for(industry_id=None, *texts: object) -> tuple[int, str, str]:
    try:
        numeric_id = int(industry_id)
    except (TypeError, ValueError):
        numeric_id = None
    haystack = " ".join("" if text is None else str(text) for text in texts)
    for code, meta in LEADING_INDUSTRIES.items():
        if numeric_id in meta["industry_ids"] or any(keyword in haystack for keyword in meta["keywords"]):
            return 1, meta["name"], code
    return 0, "", ""


def leading_label(is_leading: object) -> str:
    try:
        return "三大先导" if int(is_leading or 0) == 1 else "常规产业"
    except (TypeError, ValueError):
        return "常规产业"


def synthetic_enterprise_name(industry_name: str, code: str, enterprise_id: int) -> str:
    names = {
        "AI": ["上海智源人工智能科技有限公司", "临港智能机器人有限公司", "浦江算法科技有限公司"],
        "IC": ["上海星河芯片科技有限公司", "浦江半导体装备有限公司", "张江集成电路设计有限公司"],
        "BIOMED": ["张江生物医药研发有限公司", "上海新药创制研究有限公司", "浦东医疗器械科技有限公司"],
    }
    if code in names:
        return f"{names[code][enterprise_id % len(names[code])]}{enterprise_id:04d}"
    return f"上海{industry_name}{enterprise_id:04d}单位"


def random_enterprise_profile(rng: random.Random, district: str, is_leading: int) -> dict:
    established = date(2002, 1, 1) + timedelta(days=rng.randint(0, 7800))
    scale_factor = rng.uniform(1.15, 2.2) if is_leading else rng.uniform(0.35, 1.35)
    revenue = rng.uniform(3000, 220000) * scale_factor
    profit = revenue * rng.uniform(0.06, 0.22)
    tax = revenue * rng.uniform(0.018, 0.07)
    return {
        "is_six_key_field": int(is_leading or rng.random() < 0.18),
        "is_four_new_track": int(is_leading and rng.random() < 0.45),
        "is_five_future_industry": int(is_leading and rng.random() < 0.35),
        "registered_capital": round(rng.uniform(500, 120000) * scale_factor, 2),
        "established_date": established.isoformat(),
        "registered_address": f"上海市{district}产业园{rng.randint(1, 999)}号",
        "is_listed": int(rng.random() < (0.10 if is_leading else 0.025)),
        "is_world_500": int(rng.random() < (0.025 if is_leading else 0.004)),
        "is_china_500": int(rng.random() < (0.055 if is_leading else 0.010)),
        "is_industry_top_100": int(rng.random() < (0.18 if is_leading else 0.035)),
        "annual_revenue": round(revenue, 2),
        "annual_profit": round(profit, 2),
        "annual_tax": round(tax, 2),
    }
