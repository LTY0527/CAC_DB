# -*- coding: utf-8 -*-
from __future__ import annotations

import re


REAL_DISPLAY_MAJOR_NAMES = {
    "人工智能",
    "数据科学与大数据技术",
    "软件工程",
    "计算机科学与技术",
    "信息安全",
    "网络工程",
    "数字媒体技术",
    "集成电路设计与集成系统",
    "微电子科学与工程",
    "电子信息工程",
    "电子科学与技术",
    "通信工程",
    "光电信息科学与工程",
    "自动化",
    "金融学",
    "金融工程",
    "经济学",
    "会计学",
    "财务管理",
    "统计学",
    "国际经济与贸易",
    "财政学",
    "保险学",
    "生物医学工程",
    "生物工程",
    "制药工程",
    "药学",
    "临床医学",
    "医学影像技术",
    "护理学",
    "预防医学",
    "新能源科学与工程",
    "新能源材料与器件",
    "机械设计制造及其自动化",
    "车辆工程",
    "智能制造工程",
    "材料科学与工程",
    "金属材料工程",
    "高分子材料与工程",
    "过程装备与控制工程",
    "建筑学",
    "城乡规划",
    "土木工程",
    "交通工程",
    "环境工程",
    "给排水科学与工程",
    "法学",
    "社会学",
    "汉语言文学",
    "新闻学",
    "广播电视学",
    "档案学",
    "教育学",
    "学前教育",
    "特殊教育",
    "心理学",
    "应用心理学",
    "英语",
    "翻译",
    "德语",
    "法语",
    "西班牙语",
    "阿拉伯语",
    "工业设计",
    "产品设计",
    "环境设计",
    "美术学",
    "服装设计与工程",
    "服装与服饰设计",
    "数学与应用数学",
    "理论与应用力学",
    "工商管理",
    "历史学",
    "化学工程与工艺",
    "应用化学",
    "纺织工程",
    "复合材料与工程",
    "轻化工程",
    "电子商务",
    "俄语",
    "商务英语",
    "国际政治",
    "外交学",
    "汉语国际教育",
    "编辑出版学",
    "能源与动力工程",
    "测控技术与仪器",
    "食品科学与工程",
    "船舶与海洋工程",
    "机械工程",
    "口腔医学",
    "生物科学",
    "物理学",
    "化学",
    "地理科学",
}


TREND_TAGS_BY_MAJOR = {
    "集成电路设计与集成系统": ["集成电路"],
    "微电子科学与工程": ["集成电路"],
    "人工智能": ["人工智能"],
    "软件工程": ["软件信息"],
    "数据科学与大数据技术": ["数据智能"],
    "信息安全": ["软件信息", "数据智能"],
    "网络工程": ["软件信息"],
    "计算机科学与技术": ["软件信息", "人工智能"],
    "电子信息工程": ["电子信息"],
    "电子科学与技术": ["电子信息", "集成电路"],
    "通信工程": ["电子信息"],
    "光电信息科学与工程": ["电子信息"],
    "自动化": ["智能制造"],
    "金融工程": ["金融科技"],
    "金融学": ["金融科技"],
    "经济学": ["金融科技"],
    "统计学": ["数据智能", "金融科技"],
    "会计学": ["财经服务"],
    "财务管理": ["财经服务"],
    "生物医学工程": ["生物医药"],
    "生物工程": ["生物医药"],
    "制药工程": ["生物医药"],
    "药学": ["生物医药"],
    "临床医学": ["医疗健康"],
    "医学影像技术": ["医疗健康"],
    "新能源科学与工程": ["新能源"],
    "新能源材料与器件": ["新能源"],
    "智能制造工程": ["智能制造"],
    "机械设计制造及其自动化": ["智能制造"],
    "车辆工程": ["新能源", "智能制造"],
    "材料科学与工程": ["新材料"],
    "金属材料工程": ["新材料"],
    "高分子材料与工程": ["新材料"],
}


TREND_WEIGHT_BY_TAG = {
    "集成电路": 98,
    "人工智能": 98,
    "数据智能": 94,
    "软件信息": 92,
    "电子信息": 90,
    "金融科技": 88,
    "生物医药": 86,
    "新能源": 84,
    "智能制造": 84,
    "新材料": 78,
    "医疗健康": 76,
    "财经服务": 70,
}


TEMPLATE_PREFIX_PATTERN = re.compile(r"^(产业|服务|绿色|智能|系统|应用|现代|国际|城市|工程|信息|资源|创新|安全|低碳|健康|文化).*\d+$")
DIGIT_SUFFIX_PATTERN = re.compile(r"\d+$")


def is_valid_display_major_name(major_name: str | None) -> bool:
    name = str(major_name or "").strip()
    if not name:
        return False
    if name in REAL_DISPLAY_MAJOR_NAMES:
        return True
    if DIGIT_SUFFIX_PATTERN.search(name):
        return False
    if TEMPLATE_PREFIX_PATTERN.search(name):
        return False
    return True


def trend_tags_for_major(major_name: str | None) -> list[str]:
    return TREND_TAGS_BY_MAJOR.get(str(major_name or "").strip(), [])


def salary_rank_weight_for_major(major_name: str | None) -> float:
    tags = trend_tags_for_major(major_name)
    if not tags:
        return 55.0 if major_name in REAL_DISPLAY_MAJOR_NAMES else 0.0
    return float(max(TREND_WEIGHT_BY_TAG.get(tag, 60) for tag in tags))


def display_priority_for_major(major_name: str | None) -> int:
    name = str(major_name or "").strip()
    if name not in REAL_DISPLAY_MAJOR_NAMES:
        return 0
    return int(round(salary_rank_weight_for_major(name)))


def major_display_metadata(major_name: str | None, placeholder: bool | None = None) -> dict:
    name = str(major_name or "").strip()
    looks_like_placeholder = bool(DIGIT_SUFFIX_PATTERN.search(name) or TEMPLATE_PREFIX_PATTERN.search(name))
    if placeholder is True:
        is_real = 0
    elif placeholder is False:
        is_real = int(bool(name) and not looks_like_placeholder)
    else:
        is_real = int((name in REAL_DISPLAY_MAJOR_NAMES or bool(name)) and not looks_like_placeholder)
    is_placeholder = int((placeholder is True) or looks_like_placeholder or not is_real)
    tags = trend_tags_for_major(name)
    return {
        "is_real_display_major": is_real,
        "is_catalog_placeholder": is_placeholder,
        "display_priority": display_priority_for_major(name),
        "salary_rank_weight": salary_rank_weight_for_major(name) if is_real else 0.0,
        "industry_trend_tags": "、".join(tags),
    }
