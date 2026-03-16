import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime

fake = Faker('zh_CN')
N = 100000  # 10万条样本


def generate_full_system_data():
    print(f"🚀 开始生成上海大学试点数据集（规模：{N}，逻辑：阶梯性薪资）...")

    # 1. 生成 dim_student (对齐附件：增加学校层次与地域)
    students = []
    # 模拟附件中的 3 类办学层次
    school_levels = ['双一流建设高校', '省属重点高校', '普通本科高校']
    # 模拟 34 类生源地
    provinces = ['上海市', '江苏省', '浙江省', '安徽省', '广东省', '北京市', '四川省', '山东省']

    for i in range(1, N + 1):
        students.append({
            'student_id': i,
            'student_name': fake.name(),
            'id_card': fake.ssn(),
            'gender': random.choice([1, 2]),
            'origin_region_code': f"{310000 + random.randint(100, 999)}",  # 模拟3112类
            'origin_place': random.choice(provinces),
            'school_name': '上海大学',
            'school_level': np.random.choice(school_levels, p=[0.6, 0.3, 0.1]),
            'edu_name': np.random.choice(['专科', '本科', '硕士', '博士'], p=[0.05, 0.65, 0.25, 0.05])
        })
    df_student = pd.DataFrame(students)
    df_student.to_csv('dim_student.csv', index=False)
    print("✅ dim_student.csv 生成完毕")

    # 2. 生成 dim_company (增加企业特征)
    companies = []
    company_names = [f"上海{fake.company_suffix()}{i}" for i in range(5000)]
    for name in company_names:
        industry = random.choice(['集成电路', '人工智能', '生物医药', '其他'])
        companies.append({
            'employer_name': name,
            'company_scale': random.choice(['大型', '中型', '小型']),
            'is_top_500': np.random.choice([0, 1], p=[0.95, 0.05]),
            'strategic_tags': industry,
            'reg_capital': random.randint(100, 100000)
        })
    df_company = pd.DataFrame(companies)
    df_company.to_csv('dim_company.csv', index=False)
    print("✅ dim_company.csv 生成完毕")

    # 3. 生成 fact_academic (对齐附件：增加学科门类)
    academic = []
    # (专业代码, 专业名称, 学科门类, 专业类)
    major_map = [
        ('080901', '计算机科学与技术', '工学', '计算机类'),
        ('080902', '软件工程', '工学', '计算机类'),
        ('020101', '经济学', '经济学', '经济学类')
    ]
    for i in range(1, N + 1):
        m_code, m_name, m_top, m_mid = random.choice(major_map)
        academic.append({
            'academic_id': i,
            'student_id': i,
            'edu_level': df_student.iloc[i - 1]['edu_name'],
            'major_code': m_code,
            'major_name': m_name,
            'discipline_category': m_top,
            'major_category': m_mid,
            'skill_level': random.choice(['初级', '中级', '高级'])
        })
    df_academic = pd.DataFrame(academic)
    df_academic.to_csv('fact_academic.csv', index=False)
    print("✅ fact_academic.csv 生成完毕")

    # 4. 生成 fact_employment (阶梯化核心逻辑)
    employment = []
    start_date = datetime(2021, 1, 1)

    for i in range(1, N + 1):
        stu_info = df_student.iloc[i - 1]
        aca_info = df_academic.iloc[i - 1]

        # A. 时间因子
        random_months = random.randint(0, 62)
        emp_date = start_date + pd.DateOffset(months=random_months)

        # B. 确定产业标签
        if aca_info['major_name'] in ['计算机科学与技术', '软件工程']:
            industry_tag = np.random.choice(['三大先导', '常规产业'], p=[0.75, 0.25])
        else:
            industry_tag = np.random.choice(['三大先导', '常规产业'], p=[0.15, 0.85])

        # ==========================================================
        # C. 阶梯薪资核心算法 (阶梯性来源于系数叠加)
        # ==========================================================
        # 1. 学历基数 (Base Tier)
        base_map = {'专科': 5500, '本科': 8500, '硕士': 13000, '博士': 22000}
        salary = base_map.get(stu_info['edu_name'], 8000)

        # 2. 办学层次系数 (School Tier)
        school_mult = 1.3 if stu_info['school_level'] == '双一流建设高校' else 1.05

        # 3. 行业/溢价系数 (Industry Tier)
        industry_mult = 1.25 if industry_tag == '三大先导' else 1.0

        # 4. 技能加成
        skill_bonus = {'初级': 0, '中级': 1500, '高级': 3500}.get(aca_info['skill_level'], 0)

        # 5. 年份溢价 (LSTM 学习信号)
        year_growth = (emp_date.year - 2021) * 1000

        # 计算总额并注入正态波动 (Sigma=1000)
        final_salary = round((salary * school_mult * industry_mult) + skill_bonus + year_growth, 2)
        final_salary += round(np.random.normal(0, 1000), 2)

        # D. 构建记录
        employment.append({
            'emp_id': i,
            'student_id': i,
            'employer_name': random.choice(company_names),
            'avg_salary': max(final_salary, 5000),  # 确保不低于上海最低工资标准
            'first_insured_date': emp_date.strftime('%Y-%m-%d'),
            'leading_industry_tag': industry_tag
        })

    df_employment = pd.DataFrame(employment)
    df_employment.to_csv('fact_employment.csv', index=False)
    print(f"✅ 成功生成 10 万条具备“阶梯性特征”的数据，适配全量算法。")


if __name__ == "__main__":
    generate_full_system_data()