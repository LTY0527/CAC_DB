# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.major_display_policy import major_display_metadata

REQUIRED_MAJORS = {
    "010101": ("哲学", "哲学", "哲学类"),
    "020101": ("经济学", "经济学", "经济学类"),
    "020201K": ("财政学", "经济学", "财政学类"),
    "020301K": ("金融学", "经济学", "金融学类"),
    "020303": ("保险学", "经济学", "金融学类"),
    "020401": ("国际经济与贸易", "经济学", "经济与贸易类"),
    "030101K": ("法学", "法学", "法学类"),
    "030202": ("国际政治", "法学", "政治学类"),
    "030203": ("外交学", "法学", "政治学类"),
    "030301": ("社会学", "法学", "社会学类"),
    "030302": ("社会工作", "法学", "社会学类"),
    "040101": ("教育学", "教育学", "教育学类"),
    "040104": ("教育技术学", "教育学", "教育学类"),
    "040106": ("学前教育", "教育学", "教育学类"),
    "040108": ("特殊教育", "教育学", "教育学类"),
    "050101": ("汉语言文学", "文学", "中国语言文学类"),
    "050103": ("汉语国际教育", "文学", "中国语言文学类"),
    "050201": ("英语", "文学", "外国语言文学类"),
    "050202": ("俄语", "文学", "外国语言文学类"),
    "050203": ("德语", "文学", "外国语言文学类"),
    "050204": ("法语", "文学", "外国语言文学类"),
    "050205": ("西班牙语", "文学", "外国语言文学类"),
    "050206": ("阿拉伯语", "文学", "外国语言文学类"),
    "050261": ("翻译", "文学", "外国语言文学类"),
    "050262": ("商务英语", "文学", "外国语言文学类"),
    "050301": ("新闻学", "文学", "新闻传播学类"),
    "050302": ("广播电视学", "文学", "新闻传播学类"),
    "050305": ("编辑出版学", "文学", "新闻传播学类"),
    "060101": ("历史学", "历史学", "历史学类"),
    "070101": ("数学与应用数学", "理学", "数学类"),
    "070201": ("物理学", "理学", "物理学类"),
    "070301": ("化学", "理学", "化学类"),
    "070302": ("应用化学", "理学", "化学类"),
    "070501": ("地理科学", "理学", "地理科学类"),
    "071001": ("生物科学", "理学", "生物科学类"),
    "071101": ("心理学", "理学", "心理学类"),
    "071102": ("应用心理学", "理学", "心理学类"),
    "071201": ("统计学", "理学", "统计学类"),
    "080101": ("理论与应用力学", "工学", "力学类"),
    "080201": ("机械工程", "工学", "机械类"),
    "080202": ("机械设计制造及其自动化", "工学", "机械类"),
    "080205": ("工业设计", "工学", "机械类"),
    "080206": ("过程装备与控制工程", "工学", "机械类"),
    "080207": ("车辆工程", "工学", "机械类"),
    "080301": ("测控技术与仪器", "工学", "仪器类"),
    "080401": ("材料科学与工程", "工学", "材料类"),
    "080405": ("金属材料工程", "工学", "材料类"),
    "080407": ("高分子材料与工程", "工学", "材料类"),
    "080408": ("复合材料与工程", "工学", "材料类"),
    "080414T": ("新能源材料与器件", "工学", "材料类"),
    "080501": ("能源与动力工程", "工学", "能源动力类"),
    "080503T": ("新能源科学与工程", "工学", "能源动力类"),
    "080701": ("电子信息工程", "工学", "电子信息类"),
    "080702": ("电子科学与技术", "工学", "电子信息类"),
    "080703": ("通信工程", "工学", "电子信息类"),
    "080704": ("微电子科学与工程", "工学", "电子信息类"),
    "080705": ("光电信息科学与工程", "工学", "电子信息类"),
    "080706": ("信息工程", "工学", "电子信息类"),
    "080710T": ("集成电路设计与集成系统", "工学", "电子信息类"),
    "080714T": ("电子信息科学与技术", "工学", "电子信息类"),
    "080717T": ("人工智能", "工学", "电子信息类"),
    "080801": ("自动化", "工学", "自动化类"),
    "080901": ("计算机科学与技术", "工学", "计算机类"),
    "080902": ("软件工程", "工学", "计算机类"),
    "080903": ("网络工程", "工学", "计算机类"),
    "080904K": ("信息安全", "工学", "计算机类"),
    "080906": ("数字媒体技术", "工学", "计算机类"),
    "080910T": ("数据科学与大数据技术", "工学", "计算机类"),
    "081001": ("土木工程", "工学", "土木类"),
    "081003": ("给排水科学与工程", "工学", "土木类"),
    "081201": ("测绘工程", "工学", "测绘类"),
    "081301": ("化学工程与工艺", "工学", "化工与制药类"),
    "081302": ("制药工程", "工学", "化工与制药类"),
    "081303T": ("资源循环科学与工程", "工学", "化工与制药类"),
    "081401": ("地质工程", "工学", "地质类"),
    "081601": ("纺织工程", "工学", "纺织类"),
    "081602": ("服装设计与工程", "工学", "纺织类"),
    "081701": ("轻化工程", "工学", "轻工类"),
    "081802": ("交通工程", "工学", "交通运输类"),
    "081901": ("船舶与海洋工程", "工学", "海洋工程类"),
    "082502": ("环境工程", "工学", "环境科学与工程类"),
    "082601": ("生物医学工程", "工学", "生物医学工程类"),
    "082701": ("食品科学与工程", "工学", "食品科学与工程类"),
    "082801": ("建筑学", "工学", "建筑类"),
    "082802": ("城乡规划", "工学", "建筑类"),
    "082803": ("风景园林", "工学", "建筑类"),
    "083001": ("生物工程", "工学", "生物工程类"),
    "100101K": ("基础医学", "医学", "基础医学类"),
    "100201K": ("临床医学", "医学", "临床医学类"),
    "100301K": ("口腔医学", "医学", "口腔医学类"),
    "100401K": ("预防医学", "医学", "公共卫生与预防医学类"),
    "100701": ("药学", "医学", "药学类"),
    "101003": ("医学影像技术", "医学", "医学技术类"),
    "101101": ("护理学", "医学", "护理学类"),
    "120101": ("管理科学", "管理学", "管理科学与工程类"),
    "120102": ("信息管理与信息系统", "管理学", "管理科学与工程类"),
    "120201K": ("工商管理", "管理学", "工商管理类"),
    "120202": ("市场营销", "管理学", "工商管理类"),
    "120203K": ("会计学", "管理学", "工商管理类"),
    "120204": ("财务管理", "管理学", "工商管理类"),
    "120403": ("劳动与社会保障", "管理学", "公共管理类"),
    "120502": ("档案学", "管理学", "图书情报与档案管理类"),
    "120801": ("电子商务", "管理学", "电子商务类"),
    "130401": ("美术学", "艺术学", "美术学类"),
    "130503": ("环境设计", "艺术学", "设计学类"),
    "130504": ("产品设计", "艺术学", "设计学类"),
    "130505": ("服装与服饰设计", "艺术学", "设计学类"),
}

DISCIPLINE_CLASSES = {
    "哲学": ["哲学类"],
    "经济学": ["经济学类", "财政学类", "金融学类", "经济与贸易类"],
    "法学": ["法学类", "政治学类", "社会学类", "民族学类", "马克思主义理论类", "公安学类"],
    "教育学": ["教育学类", "体育学类"],
    "文学": ["中国语言文学类", "外国语言文学类", "新闻传播学类"],
    "历史学": ["历史学类"],
    "理学": ["数学类", "物理学类", "化学类", "天文学类", "地理科学类", "大气科学类", "海洋科学类", "地球物理学类", "地质学类", "生物科学类", "心理学类", "统计学类"],
    "工学": ["力学类", "机械类", "仪器类", "材料类", "能源动力类", "电气类", "电子信息类", "自动化类", "计算机类", "土木类", "水利类", "测绘类", "化工与制药类", "地质类", "矿业类", "纺织类", "轻工类", "交通运输类", "海洋工程类", "航空航天类", "兵器类", "核工程类", "农业工程类", "林业工程类", "环境科学与工程类", "生物医学工程类", "食品科学与工程类", "建筑类", "安全科学与工程类", "生物工程类", "公安技术类", "交叉工程类"],
    "农学": ["植物生产类", "自然保护与环境生态类", "动物生产类", "动物医学类", "林学类", "水产类", "草学类"],
    "医学": ["基础医学类", "临床医学类", "口腔医学类", "公共卫生与预防医学类", "中医学类", "中西医结合类", "药学类", "中药学类", "法医学类", "医学技术类", "护理学类"],
    "管理学": ["管理科学与工程类", "工商管理类", "农业经济管理类", "公共管理类", "图书情报与档案管理类", "物流管理与工程类", "工业工程类", "电子商务类", "旅游管理类"],
    "艺术学": ["艺术学理论类", "音乐与舞蹈学类", "戏剧与影视学类", "美术学类", "设计学类"],
}

ROOTS = ["智能", "数字", "应用", "现代", "国际", "城市", "产业", "工程", "信息", "资源", "系统", "创新", "服务", "安全", "绿色", "低碳", "健康", "文化"]


def degree_type(discipline: str) -> str:
    return discipline


def policy_tags(name: str, major_class: str) -> str:
    text = name + major_class
    mapping = [
        ("人工智能", "人工智能"),
        ("数据", "数据要素"),
        ("集成电路", "集成电路"),
        ("新能源", "新能源"),
        ("智能", "智能制造"),
        ("护理", "护理康养"),
        ("医学", "医疗健康"),
        ("环境", "绿色低碳"),
        ("数字媒体", "数字文化"),
        ("金融", "金融科技"),
        ("国际", "国际传播"),
    ]
    tags = [value for key, value in mapping if key in text]
    return "、".join(dict.fromkeys(tags)) if tags else "常规专业"


def generate_major_catalog() -> list[dict]:
    rows = []
    used_names = set()
    used_codes = set()
    for code, (name, discipline, major_class) in sorted(REQUIRED_MAJORS.items()):
        rows.append({
            "major_code": code,
            "major_name": name,
            "discipline_category": discipline,
            "major_class": major_class,
            "degree_type": degree_type(discipline),
            "study_years": 5 if discipline == "医学" and code.endswith("K") else 4,
            "is_controlled": int(code.endswith("K")),
            "is_special": int(code.endswith("T")),
            "is_new_strategy_major": int(policy_tags(name, major_class) != "常规专业"),
            "policy_direction_tags": policy_tags(name, major_class),
            **major_display_metadata(name, placeholder=False),
        })
        used_names.add(name)
        used_codes.add(code)

    classes = [(discipline, cls) for discipline, cls_list in DISCIPLINE_CLASSES.items() for cls in cls_list]
    class_counts = {cls: 0 for _, cls in classes}
    serial = 1
    idx = 0
    while len(rows) < 845:
        discipline, major_class = classes[idx % len(classes)]
        idx += 1
        root = ROOTS[(serial + idx) % len(ROOTS)]
        base = major_class.replace("类", "")
        suffix = "工程" if discipline == "工学" and "工程" not in base else ("管理" if discipline == "管理学" and "管理" not in base else ("学" if discipline not in {"工学", "艺术学"} and not base.endswith("学") else ""))
        class_counts[major_class] += 1
        name = f"{root}{base}{suffix}{class_counts[major_class]}"
        code_prefix = {"哲学": "01", "经济学": "02", "法学": "03", "教育学": "04", "文学": "05", "历史学": "06", "理学": "07", "工学": "08", "农学": "09", "医学": "10", "管理学": "12", "艺术学": "13"}[discipline]
        code = f"{code_prefix}{serial:04d}"
        serial += 1
        if name in used_names or code in used_codes:
            continue
        rows.append({
            "major_code": code,
            "major_name": name,
            "discipline_category": discipline,
            "major_class": major_class,
            "degree_type": degree_type(discipline),
            "study_years": 5 if discipline == "医学" else 4,
            "is_controlled": 0,
            "is_special": 0,
            "is_new_strategy_major": int(any(key in name for key in ["智能", "数字", "新能源", "安全", "绿色"])),
            "policy_direction_tags": policy_tags(name, major_class),
            **major_display_metadata(name, placeholder=True),
        })
        used_names.add(name)
        used_codes.add(code)

    validate_major_catalog(rows)
    return rows


def validate_major_catalog(rows: list[dict]) -> None:
    if len(rows) != 845:
        raise ValueError(f"dim_major_catalog must contain 845 rows, got {len(rows)}")
    if len({row["discipline_category"] for row in rows}) != 12:
        raise ValueError("dim_major_catalog must cover 12 disciplines")
    if len({row["major_class"] for row in rows}) != 93:
        raise ValueError("dim_major_catalog must cover 93 major classes")
    if len({row["major_code"] for row in rows}) != len(rows):
        raise ValueError("major_code must be unique")
    if len({row["major_name"] for row in rows}) != len(rows):
        raise ValueError("major_name must be unique")
    names = {row["major_name"] for row in rows}
    missing = sorted(name for _, (name, _, _) in REQUIRED_MAJORS.items() if name not in names)
    if missing:
        raise ValueError(f"required majors missing: {missing}")


if __name__ == "__main__":
    data = generate_major_catalog()
    print(len(data), len({r["discipline_category"] for r in data}), len({r["major_class"] for r in data}))
