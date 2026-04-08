import random
import json
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

fake = Faker("zh_CN")
SEED = 20260324
N = 100000
CREATED_AT = "2026-03-24 20:15:02"
START_DATE = datetime(2024, 7, 1)
END_DATE = datetime(2026, 3, 31)

random.seed(SEED)
Faker.seed(SEED)

_MAJOR_ROWS = [
    ("010101","哲学","哲学","哲学类","教育科研"),("010102","逻辑学","哲学","哲学类","教育科研"),("010103","宗教学","哲学","哲学类","公共服务"),("010104","伦理学","哲学","哲学类","公共服务"),
    ("020101","经济学","经济学","经济学类","现代金融"),("020102","经济统计学","经济学","经济学类","现代金融"),("020103","国民经济管理","经济学","经济学类","现代金融"),("020104","资源与环境经济学","经济学","经济学类","绿色低碳"),("020105","商务经济学","经济学","经济学类","现代商贸"),("020106","数字经济","经济学","经济学类","人工智能"),
    ("020201","财政学","经济学","财政学类","现代金融"),("020202","税收学","经济学","财政学类","现代金融"),("020301","金融学","经济学","金融学类","现代金融"),("020302","金融工程","经济学","金融学类","现代金融"),("020303","保险学","经济学","金融学类","现代金融"),("020304","投资学","经济学","金融学类","现代金融"),("020305","信用管理","经济学","金融学类","现代金融"),("020401","国际经济与贸易","经济学","经济与贸易类","现代商贸"),("020402","贸易经济","经济学","经济与贸易类","现代商贸"),
    ("030101","法学","法学","法学类","公共服务"),("030102","知识产权","法学","法学类","现代服务"),("030103","监狱学","法学","法学类","公共服务"),("030201","政治学与行政学","法学","政治学类","公共服务"),("030202","国际政治","法学","政治学类","公共服务"),("030301","社会学","法学","社会学类","公共服务"),("030302","社会工作","法学","社会学类","公共服务"),("030401","民族学","法学","民族学类","公共服务"),
    ("040101","教育学","教育学","教育学类","教育科研"),("040102","科学教育","教育学","教育学类","教育科研"),("040103","人文教育","教育学","教育学类","教育科研"),("040104","教育技术学","教育学","教育学类","教育科研"),("040105","艺术教育","教育学","教育学类","教育科研"),("040106","学前教育","教育学","教育学类","教育科研"),("040107","小学教育","教育学","教育学类","教育科研"),("040108","特殊教育","教育学","教育学类","教育科研"),
    ("050101","汉语言文学","文学","中国语言文学类","文化传媒"),("050102","汉语言","文学","中国语言文学类","文化传媒"),("050103","秘书学","文学","中国语言文学类","现代服务"),("050201","英语","文学","外国语言文学类","国际商务"),("050202","俄语","文学","外国语言文学类","国际商务"),("050203","德语","文学","外国语言文学类","国际商务"),("050204","法语","文学","外国语言文学类","国际商务"),("050205","日语","文学","外国语言文学类","国际商务"),("050206","翻译","文学","外国语言文学类","现代服务"),("050301","新闻学","文学","新闻传播学类","文化传媒"),("050302","广播电视学","文学","新闻传播学类","文化传媒"),("050303","广告学","文学","新闻传播学类","文化传媒"),("050304","传播学","文学","新闻传播学类","文化传媒"),
    ("060101","历史学","历史学","历史学类","教育科研"),("060102","世界史","历史学","历史学类","教育科研"),("060103","考古学","历史学","历史学类","文化传媒"),
    ("070101","数学与应用数学","理学","数学类","人工智能"),("070102","信息与计算科学","理学","数学类","人工智能"),("070201","物理学","理学","物理学类","集成电路"),("070202","应用物理学","理学","物理学类","集成电路"),("070301","化学","理学","化学类","生物医药"),("070302","应用化学","理学","化学类","新材料"),("070401","天文学","理学","天文学类","科研机构"),("070501","地理科学","理学","地理科学类","城市规划"),("070601","大气科学","理学","大气科学类","绿色低碳"),("070701","海洋科学","理学","海洋科学类","科研机构"),("070801","地球物理学","理学","地球物理学类","科研机构"),("070901","生物科学","理学","生物科学类","生物医药"),("071001","心理学","理学","心理学类","医疗健康"),("071101","统计学","理学","统计学类","人工智能"),
    ("080101","理论与应用力学","工学","力学类","高端装备"),("080201","机械工程","工学","机械类","高端装备"),("080202","机械设计制造及其自动化","工学","机械类","智能制造"),("080203","材料成型及控制工程","工学","机械类","智能制造"),("080204","工业设计","工学","机械类","高端装备"),("080301","测控技术与仪器","工学","仪器类","智能制造"),("080401","材料科学与工程","工学","材料类","新材料"),("080402","材料物理","工学","材料类","新材料"),("080403","材料化学","工学","材料类","新材料"),("080411","环境工程","工学","环境科学与工程类","绿色低碳"),("080501","能源与动力工程","工学","能源动力类","绿色低碳"),("080601","电气工程及其自动化","工学","电气类","智能制造"),("080701","电子信息工程","工学","电子信息类","集成电路"),("080702","电子科学与技术","工学","电子信息类","集成电路"),("080703","通信工程","工学","电子信息类","人工智能"),("080704","微电子科学与工程","工学","电子信息类","集成电路"),("080705","光电信息科学与工程","工学","电子信息类","集成电路"),("080706","信息工程","工学","电子信息类","人工智能"),("080801","自动化","工学","自动化类","人工智能"),("080901","计算机科学与技术","工学","计算机类","人工智能"),("080902","软件工程","工学","计算机类","人工智能"),("080903","网络工程","工学","计算机类","人工智能"),("080904","信息安全","工学","计算机类","人工智能"),("080905","物联网工程","工学","计算机类","人工智能"),("080906","数据科学与大数据技术","工学","计算机类","人工智能"),("080907","智能科学与技术","工学","计算机类","人工智能"),("081001","土木工程","工学","土木类","建筑工程"),("081002","建筑环境与能源应用工程","工学","土木类","建筑工程"),("081003","给排水科学与工程","工学","土木类","建筑工程"),("081301","化学工程与工艺","工学","化工与制药类","生物医药"),("081302","制药工程","工学","化工与制药类","生物医药"),("081303","资源循环科学与工程","工学","化工与制药类","绿色低碳"),("081401","地质工程","工学","地质类","城市建设"),("081601","纺织工程","工学","纺织类","时尚消费"),("081602","服装设计与工程","工学","纺织类","时尚消费"),("081603","轻化工程","工学","轻工类","消费品制造"),("081801","交通运输","工学","交通运输类","现代物流"),("081802","交通工程","工学","交通运输类","城市规划"),("082701","食品科学与工程","工学","食品科学与工程类","消费品制造"),("082801","建筑学","工学","建筑类","建筑设计"),("082802","城乡规划","工学","建筑类","城市规划"),("082803","风景园林","工学","建筑类","城市规划"),("082901","安全工程","工学","安全科学与工程类","工业安全"),
    ("090101","农学","农学","植物生产类","现代农业"),("090201","园艺","农学","植物生产类","现代农业"),("090301","植物保护","农学","自然保护与环境生态类","现代农业"),("090401","动物医学","农学","动物生产类","医疗健康"),
    ("100101","基础医学","医学","基础医学类","生物医药"),("100201","临床医学","医学","临床医学类","医疗健康"),("100202","麻醉学","医学","临床医学类","医疗健康"),("100203","医学影像学","医学","临床医学类","医疗健康"),("100401","预防医学","医学","公共卫生与预防医学类","医疗健康"),("100701","药学","医学","药学类","生物医药"),("100702","药物制剂","医学","药学类","生物医药"),("100703","临床药学","医学","药学类","生物医药"),
    ("120101","管理科学","管理学","管理科学与工程类","现代服务"),("120102","信息管理与信息系统","管理学","管理科学与工程类","人工智能"),("120201","工商管理","管理学","工商管理类","现代服务"),("120202","市场营销","管理学","工商管理类","现代商贸"),("120203","会计学","管理学","工商管理类","现代金融"),("120204","财务管理","管理学","工商管理类","现代金融"),("120205","审计学","管理学","工商管理类","现代金融"),("120401","公共事业管理","管理学","公共管理类","公共服务"),("120402","行政管理","管理学","公共管理类","公共服务"),("120403","劳动与社会保障","管理学","公共管理类","公共服务"),("120601","物流管理","管理学","物流管理与工程类","现代物流"),("120701","工业工程","管理学","工业工程类","智能制造"),("120801","电子商务","管理学","电子商务类","现代商贸"),
    ("130101","艺术史论","艺术学","艺术学理论类","文化传媒"),("130201","音乐表演","艺术学","音乐与舞蹈学类","文化传媒"),("130401","美术学","艺术学","美术学类","文化传媒"),("130501","艺术设计学","艺术学","设计学类","文化传媒"),("130502","视觉传达设计","艺术学","设计学类","文化传媒"),
]

MAJOR_POOL = [{"major_code": a, "major_name": b, "discipline_category": c, "major_category": d, "industry_target": e} for a, b, c, d, e in _MAJOR_ROWS]
EXCLUDED_MAJOR_CODES = {
    "010102", "010103", "020103", "020104", "020105", "020202", "020303", "020304",
    "030102", "030103", "030202", "030302", "030401", "040102", "040103", "040105",
    "050102", "050103", "050202", "050203", "050204", "060103", "070102", "070401",
    "070601", "070701", "070801", "080101", "080203", "080204", "080301", "081002",
    "090201", "090301", "100202", "100203",
}
MAJOR_POOL = [item for item in MAJOR_POOL if item["major_code"] not in EXCLUDED_MAJOR_CODES]
if len(MAJOR_POOL) != 102:
    raise ValueError(f"MAJOR_POOL must contain 102 majors, got {len(MAJOR_POOL)}")

SCHOOL_CONFIG = {
    "复旦大学": {"school_level": "双一流建设高校", "school_mult": 1.24, "student_weight": 0.13, "featured_majors": ["临床医学", "基础医学", "数学与应用数学", "金融学", "新闻学"]},
    "上海交通大学": {"school_level": "双一流建设高校", "school_mult": 1.26, "student_weight": 0.14, "featured_majors": ["计算机科学与技术", "软件工程", "临床医学", "机械工程", "电子信息工程"]},
    "同济大学": {"school_level": "双一流建设高校", "school_mult": 1.18, "student_weight": 0.11, "featured_majors": ["土木工程", "建筑学", "城乡规划", "交通工程", "环境工程"]},
    "华东师范大学": {"school_level": "双一流建设高校", "school_mult": 1.15, "student_weight": 0.10, "featured_majors": ["教育学", "小学教育", "心理学", "汉语言文学", "统计学"]},
    "上海大学": {"school_level": "市属重点高校", "school_mult": 1.08, "student_weight": 0.10, "featured_majors": ["机械工程", "电子信息工程", "美术学", "社会学", "材料科学与工程"]},
    "上海财经大学": {"school_level": "双一流建设高校", "school_mult": 1.16, "student_weight": 0.08, "featured_majors": ["金融学", "金融工程", "会计学", "财务管理", "经济学"]},
    "东华大学": {"school_level": "双一流建设高校", "school_mult": 1.11, "student_weight": 0.08, "featured_majors": ["材料科学与工程", "纺织工程", "服装设计与工程", "轻化工程", "应用化学"]},
    "华东理工大学": {"school_level": "双一流建设高校", "school_mult": 1.12, "student_weight": 0.09, "featured_majors": ["化学工程与工艺", "制药工程", "材料科学与工程", "应用化学", "信息管理与信息系统"]},
    "上海师范大学": {"school_level": "市属重点高校", "school_mult": 1.03, "student_weight": 0.09, "featured_majors": ["汉语言文学", "教育学", "学前教育", "英语", "历史学"]},
    "上海工程技术大学": {"school_level": "应用型本科高校", "school_mult": 0.98, "student_weight": 0.08, "featured_majors": ["机械设计制造及其自动化", "交通运输", "自动化", "物流管理", "工商管理"]},
}

FEATURED_MAJOR_INDUSTRY_OVERRIDE = {
    "复旦大学": {"临床医学": "生物医药", "基础医学": "生物医药", "数学与应用数学": "人工智能", "金融学": "现代金融", "新闻学": "文化传媒"},
    "上海交通大学": {"计算机科学与技术": "人工智能", "软件工程": "人工智能", "临床医学": "生物医药", "机械工程": "智能制造", "电子信息工程": "集成电路"},
    "同济大学": {"土木工程": "建筑工程", "建筑学": "建筑设计", "城乡规划": "城市规划", "交通工程": "城市规划", "环境工程": "绿色低碳"},
    "华东师范大学": {"教育学": "教育科研", "小学教育": "教育科研", "心理学": "医疗健康", "汉语言文学": "教育科研", "统计学": "人工智能"},
    "上海大学": {"机械工程": "智能制造", "电子信息工程": "集成电路", "美术学": "文化传媒", "社会学": "公共服务", "材料科学与工程": "新材料"},
    "上海财经大学": {"金融学": "现代金融", "金融工程": "现代金融", "会计学": "现代金融", "财务管理": "现代金融", "经济学": "现代金融"},
    "东华大学": {"材料科学与工程": "新材料", "纺织工程": "时尚消费", "服装设计与工程": "时尚消费", "轻化工程": "消费品制造", "应用化学": "新材料"},
    "华东理工大学": {"化学工程与工艺": "生物医药", "制药工程": "生物医药", "材料科学与工程": "新材料", "应用化学": "新材料", "信息管理与信息系统": "人工智能"},
    "上海师范大学": {"汉语言文学": "教育科研", "教育学": "教育科研", "学前教育": "教育科研", "英语": "教育科研", "历史学": "教育科研"},
    "上海工程技术大学": {"机械设计制造及其自动化": "智能制造", "交通运输": "现代物流", "自动化": "智能制造", "物流管理": "现代物流", "工商管理": "现代服务"},
}

INDUSTRY_CONFIG = {
    "集成电路": {"tag": "三大先导", "mult": 1.30}, "人工智能": {"tag": "三大先导", "mult": 1.28}, "生物医药": {"tag": "三大先导", "mult": 1.27},
    "现代金融": {"tag": "常规产业", "mult": 1.16}, "智能制造": {"tag": "常规产业", "mult": 1.12}, "建筑工程": {"tag": "常规产业", "mult": 1.05},
    "建筑设计": {"tag": "常规产业", "mult": 1.08}, "城市规划": {"tag": "常规产业", "mult": 1.06}, "教育科研": {"tag": "常规产业", "mult": 0.94},
    "文化传媒": {"tag": "常规产业", "mult": 0.96}, "公共服务": {"tag": "常规产业", "mult": 0.92}, "现代服务": {"tag": "常规产业", "mult": 1.00},
    "现代商贸": {"tag": "常规产业", "mult": 1.01}, "现代物流": {"tag": "常规产业", "mult": 1.00}, "医疗健康": {"tag": "常规产业", "mult": 1.10},
    "高端装备": {"tag": "常规产业", "mult": 1.08}, "新材料": {"tag": "常规产业", "mult": 1.14}, "绿色低碳": {"tag": "常规产业", "mult": 1.03},
    "消费品制造": {"tag": "常规产业", "mult": 0.98}, "时尚消费": {"tag": "常规产业", "mult": 0.99}, "国际商务": {"tag": "常规产业", "mult": 1.02},
    "工业安全": {"tag": "常规产业", "mult": 1.01},
    "科研机构": {"tag": "常规产业", "mult": 1.04},
    "城市建设": {"tag": "常规产业", "mult": 1.02},
    "现代农业": {"tag": "常规产业", "mult": 0.95},
}

ORIGIN_REGIONS = [
    {"origin_region_code": "310000", "origin_place": "上海市"}, {"origin_region_code": "320000", "origin_place": "江苏省"},
    {"origin_region_code": "330000", "origin_place": "浙江省"}, {"origin_region_code": "340000", "origin_place": "安徽省"},
    {"origin_region_code": "360000", "origin_place": "江西省"}, {"origin_region_code": "370000", "origin_place": "山东省"},
    {"origin_region_code": "410000", "origin_place": "河南省"}, {"origin_region_code": "420000", "origin_place": "湖北省"},
    {"origin_region_code": "430000", "origin_place": "湖南省"}, {"origin_region_code": "440000", "origin_place": "广东省"},
    {"origin_region_code": "500000", "origin_place": "重庆市"}, {"origin_region_code": "510000", "origin_place": "四川省"},
]

BASE_SALARY = {"本科": 9800, "硕士": 15800, "博士": 24500}
SKILL_MULT = {"初": 0.92, "中": 1.00, "高": 1.12}
LEADING_INDUSTRIES = {"集成电路", "人工智能", "生物医药"}


def _lookup():
    return {m["major_name"]: m for m in MAJOR_POOL}


def build_school_major_map():
    major_lookup = _lookup()
    featured_all = set()
    result = {}
    non_feature_pool = MAJOR_POOL.copy()
    for school, cfg in SCHOOL_CONFIG.items():
        featured = [major_lookup[name] for name in cfg["featured_majors"]]
        featured_all.update(cfg["featured_majors"])
        feat_codes = {m["major_code"] for m in featured}
        general = random.sample([m for m in non_feature_pool if m["major_code"] not in feat_codes], 20 - len(featured))
        result[school] = {"featured": featured, "general": general}
    return result


def build_employer_pool():
    pool = {}
    company_rows = []
    company_id = 1
    scale_weights = [0.18, 0.52, 0.30]
    for industry in INDUSTRY_CONFIG:
        names = []
        for i in range(1, 81):
            employer_name = f"上海{fake.company_prefix()}{industry}{fake.company_suffix()}{i:03d}"
            names.append(employer_name)
            is_top_500 = int(random.random() < (0.12 if industry in LEADING_INDUSTRIES else 0.05))
            is_listed = int(random.random() < (0.20 if industry in LEADING_INDUSTRIES else 0.09))
            company_scale = random.choices(["大型", "中型", "小型"], weights=scale_weights, k=1)[0]
            reg_capital = round(random.uniform(5000, 80000) * (1.45 if is_top_500 else 1.0), 2)
            last_year_revenue = round(reg_capital * random.uniform(1.8, 6.5), 2)
            strategic_tags = [industry]
            if INDUSTRY_CONFIG[industry]["tag"] == "三大先导":
                strategic_tags.append("三大先导")
            if is_top_500:
                strategic_tags.append("500强")
            company_rows.append({
                "company_id": company_id,
                "employer_name": employer_name,
                "company_scale": company_scale,
                "is_top_500": is_top_500,
                "is_listed": is_listed,
                "strategic_tags": json.dumps(strategic_tags, ensure_ascii=False),
                "reg_capital": reg_capital,
                "last_year_revenue": last_year_revenue,
            })
            company_id += 1
        pool[industry] = names
    return pool, company_rows


def pick_major(school, school_major_map):
    if random.random() < 0.6:
        return random.choice(school_major_map[school]["featured"]), True
    return random.choice(school_major_map[school]["general"]), False


def infer_industry(school, major, is_featured):
    base = major["industry_target"]
    aligned = FEATURED_MAJOR_INDUSTRY_OVERRIDE.get(school, {}).get(major["major_name"], base)
    if is_featured:
        return random.choices([aligned, base], weights=[0.82, 0.18] if aligned in LEADING_INDUSTRIES else [0.72, 0.28], k=1)[0]
    if base in LEADING_INDUSTRIES:
        return random.choices([base, "现代服务", "智能制造"], weights=[0.68, 0.18, 0.14], k=1)[0]
    return base if random.random() < 0.82 else random.choice(list(INDUSTRY_CONFIG.keys()))


def sh_status(school, school_level, edu_name, industry_tag):
    if school in {"复旦大学", "上海交通大学"} and industry_tag == "三大先导":
        p = 0.89
    elif school_level == "应用型本科高校" and edu_name == "本科":
        p = 0.68
    elif school_level == "市属重点高校" and edu_name == "本科":
        p = 0.71
    elif school_level == "双一流建设高校" and edu_name == "本科":
        p = 0.79
    elif edu_name == "硕士":
        p = 0.81 if industry_tag == "三大先导" else 0.76
    else:
        p = 0.85 if industry_tag == "三大先导" else 0.78
    return int(random.random() < p)


def calc_salary(edu_name, school_mult, industry_mult, skill_level, featured_match):
    base = BASE_SALARY[edu_name]
    skill_mult = SKILL_MULT[skill_level]
    premium = 1.28 if featured_match else 1.0
    noise = random.gauss(0, 900 if edu_name == "本科" else 1300)
    return round(max(base * school_mult * industry_mult * skill_mult * premium + noise, 6500), 2)


def insured_date():
    return (START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))).strftime("%Y-%m-%d")


def generate_full_system_data():
    school_major_map = build_school_major_map()
    employer_pool, company_rows = build_employer_pool()
    school_names = list(SCHOOL_CONFIG.keys())
    school_weights = [SCHOOL_CONFIG[s]["student_weight"] for s in school_names]
    students, academics, employments = [], [], []

    for sid in range(1, N + 1):
        school = random.choices(school_names, weights=school_weights, k=1)[0]
        cfg = SCHOOL_CONFIG[school]
        origin = random.choice(ORIGIN_REGIONS)
        edu_name = random.choices(["本科", "硕士", "博士"], weights=[0.72, 0.22, 0.06], k=1)[0]
        major, is_featured = pick_major(school, school_major_map)
        industry = infer_industry(school, major, is_featured)
        industry_cfg = INDUSTRY_CONFIG[industry]
        aligned = FEATURED_MAJOR_INDUSTRY_OVERRIDE.get(school, {}).get(major["major_name"], major["industry_target"])
        featured_match = is_featured and industry == aligned
        skill = random.choices(["初", "中", "高"], weights=[0.28, 0.47, 0.25], k=1)[0]

        students.append({
            "student_id": sid, "student_name": fake.name(), "id_card": fake.ssn(), "gender": random.choice(["男", "女"]),
            "origin_region_code": origin["origin_region_code"], "origin_place": origin["origin_place"], "created_at": CREATED_AT,
            "school_name": school, "school_level": cfg["school_level"], "edu_name": edu_name,
        })
        academics.append({
            "academic_id": sid, "student_id": sid, "edu_level": edu_name, "major_code": major["major_code"], "major_name": major["major_name"],
            "discipline_category": major["discipline_category"], "major_category": major["major_category"], "skill_level": skill,
        })
        employments.append({
            "emp_id": sid, "student_id": sid, "employer_name": random.choice(employer_pool[industry]),
            "avg_salary": calc_salary(edu_name, cfg["school_mult"], industry_cfg["mult"], skill, featured_match),
            "first_insured_date": insured_date(), "sh_insurance_status": sh_status(school, cfg["school_level"], edu_name, industry_cfg["tag"]),
            "leading_industry_tag": industry_cfg["tag"],
        })

    df_student = pd.DataFrame(students)
    df_academic = pd.DataFrame(academics)
    df_company = pd.DataFrame(company_rows)
    df_employment = pd.DataFrame(employments)
    df_student.to_csv("dim_student.csv", index=False, encoding="utf-8-sig")
    df_academic.to_csv("fact_academic.csv", index=False, encoding="utf-8-sig")
    df_company.to_csv("dim_company.csv", index=False, encoding="utf-8-sig")
    df_employment.to_csv("fact_employment.csv", index=False, encoding="utf-8-sig")

    merged = df_student[["student_id", "school_name", "school_level", "edu_name"]].merge(df_employment, on="student_id")
    elite_rate = merged[(merged["school_name"].isin(["复旦大学", "上海交通大学"])) & (merged["leading_industry_tag"] == "三大先导")]["sh_insurance_status"].mean()
    ordinary_rate = merged[(merged["school_level"] == "应用型本科高校") & (merged["edu_name"] == "本科")]["sh_insurance_status"].mean()
    print(f"生成完成，共 {N} 条样本")
    print("输出文件: dim_student.csv, fact_academic.csv, dim_company.csv, fact_employment.csv")
    print(f"复旦/交大在三大先导产业留沪率: {elite_rate:.4f}")
    print(f"普通本科留沪率: {ordinary_rate:.4f}")

def validate_schema_integrity():
    missing_industries = {
        major["industry_target"]
        for major in MAJOR_POOL
        if major["industry_target"] not in INDUSTRY_CONFIG
    }

    if missing_industries:
        raise ValueError(
            "Schema integrity validation failed. Missing industries in "
            f"INDUSTRY_CONFIG: {sorted(missing_industries)}"
        )

if __name__ == "__main__":
    validate_schema_integrity()
    generate_full_system_data()
