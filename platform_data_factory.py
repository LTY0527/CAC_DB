import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime
from datetime import datetime, timedelta
# 初始化
fake = Faker('zh_CN')
N = 100000


def generate_full_system_data():
    print(f"🚀 开始生成上海高校模拟数据集（规模：{N}）...")

    # --- 1. 配置映射表（确保专业名称与后续逻辑对齐） ---
    school_config = {
        '复旦大学': ('双一流建设高校', {
            '010101': ('哲学', '哲学', '哲学类', 0.4),
            '030201': ('政治学与行政学', '法学', '政治学类', 0.3),
            '070101': ('数学与应用数学', '理学', '数学类', 0.3)
        }),
        '上海交通大学': ('双一流建设高校', {
            '080202': ('机械工程', '工学', '机械类', 0.4),
            '080701': ('计算机科学与技术', '工学', '计算机类', 0.3),  # 修正名称以匹配逻辑
            '100201K': ('临床医学', '医学', '临床医学类', 0.3)
        }),
        '同济大学': ('双一流建设高校', {
            '081001': ('土木工程', '工学', '土木类', 0.5),
            '082801': ('建筑学', '工学', '建筑类', 0.3),
            '082301': ('交通运输', '工学', '交通运输类', 0.2)
        }),
        '华东理工大学': ('双一流建设高校', {
            '081301': ('化学工程与工艺', '工学', '化工与制药类', 1.0)
        }),
        '上海财经大学': ('双一流建设高校', {
            '020301K': ('金融学', '经济学', '金融学类', 1.0)
        })
    }

    # 辅助列表
    school_names = list(school_config.keys())
    provinces = ['上海市', '江苏省', '浙江省', '安徽省', '广东省', '北京市', '四川省', '山东省']

    # --- 2. 生成 dim_student ---
    print("📦 正在生成学生维度表...")
    student_list = []
    for i in range(1, N + 1):
        s_name = random.choice(school_names)
        student_list.append({
            'student_id': i,
            'student_name': fake.name(),
            'id_card': fake.ssn(),
            'gender': random.choice([1, 2]),
            'origin_place': random.choice(provinces),
            'school_name': s_name,
            'school_level': school_config[s_name][0],
            'edu_name': np.random.choice(['本科', '硕士', '博士'], p=[0.6, 0.3, 0.1])
        })
    df_student = pd.DataFrame(student_list)

    # --- 3. 生成 fact_academic (学术事实) ---
    print("📚 正在生成学术事实表...")
    academic_list = []
    for i, row in df_student.iterrows():
        majors = school_config[row['school_name']][1]
        m_codes = list(majors.keys())
        m_weights = [m[3] for m in majors.values()]
        chosen_code = np.random.choice(m_codes, p=m_weights)
        m_info = majors[chosen_code]

        academic_list.append({
            'student_id': row['student_id'],
            'major_code': chosen_code,
            'major_name': m_info[0],
            'discipline_category': m_info[1],
            'skill_level': random.choice(['初级', '中级', '高级'])
        })
    df_academic = pd.DataFrame(academic_list)

    # --- 4. 生成 dim_company (公司维度) ---
    print("🏢 正在生成企业维度表...")
    companies = []
    industries = ['集成电路', '人工智能', '生物医药', '金融贸易', '智能制造', '常规产业']
    for i in range(5000):
        companies.append({
            'employer_name': f"上海{fake.company_prefix()}_{i}",
            'industry': random.choice(industries),
            'is_top_500': np.random.choice([0, 1], p=[0.95, 0.05])
        })
    df_company = pd.DataFrame(companies)

    # --- 5. 生成 fact_employment (采用向量化逻辑) ---
    print("💰 正在基于学术背景执行向量化薪资计算...")

    # 合并中间表以进行统一计算
    df_full = df_student.merge(df_academic, on='student_id')

    # A. 基础起薪映射
    base_salary_map = {'本科': 8500, '硕士': 13500, '博士': 22000}
    df_full['salary_base'] = df_full['edu_name'].map(base_salary_map)

    # B. 学校溢价系数
    df_full['school_mult'] = np.where(df_full['school_name'].isin(['复旦大学', '上海交通大学']), 1.3, 1.1)

    # C. 行业逻辑矩阵 (核心匹配)
    industry_premium = {
        '金融学': 1.4,
        '计算机科学与技术': 1.5,
        '临床医学': 1.3,
        '化学工程与工艺': 1.2
    }
    df_full['industry_mult'] = df_full['major_name'].map(industry_premium).fillna(1.0)

    # D. 技能等级加成
    skill_map = {'初级': 0, '中级': 2000, '高级': 4500}
    df_full['skill_bonus'] = df_full['skill_level'].map(skill_map)

    # E. 最终计算 + 随机噪声
    start_date = datetime(2021, 1, 1)
    df_full['random_months'] = [random.randint(0, 60) for _ in range(N)]
    df_full['emp_year'] = df_full['random_months'].apply(lambda x: (start_date + pd.DateOffset(months=x)).year)

    # 薪资公式：(基数 * 学校系数 * 行业系数 * 通胀) + 技能加成 + 噪声
    inflation = 1 + (df_full['emp_year'] - 2021) * 0.05
    noise = np.random.normal(0, 1200, N)

    df_full['avg_salary'] = (df_full['salary_base'] * df_full['school_mult'] * df_full['industry_mult'] * inflation) + \
                            df_full['skill_bonus'] + noise

    # 模拟入职日期：在 2021-01-01 到 2026-03-31 之间随机分布
    start_date = datetime(2021, 1, 1)
    end_date = datetime(2026, 3, 31)
    delta_days = (end_date - start_date).days

    # 生成 N 个随机日期
    random_dates = [
        (start_date + timedelta(days=random.randint(0, delta_days))).strftime('%Y-%m-%d')
        for _ in range(N)
    ]

    # 修正后的 df_employment 构造
    df_employment = pd.DataFrame({
        'emp_id': range(1, N + 1),
        'student_id': df_full['student_id'],
        'employer_name': [random.choice(df_company['employer_name'].values) for _ in range(N)],
        'avg_salary': df_full['avg_salary'].clip(lower=6000).round(2),
        'first_insured_date': random_dates,  # <--- 补全这个缺失字段
        'leading_industry_tag': np.where(df_full['industry_mult'] > 1.0, '三大先导', '常规产业')
    })

    # --- 6. 存储结果 ---
    df_student.to_csv('dim_student.csv', index=False)
    df_academic.to_csv('fact_academic.csv', index=False)
    df_company.to_csv('dim_company.csv', index=False)
    df_employment.to_csv('fact_employment.csv', index=False)

    print(f"\n✅ 数据生成任务圆满完成！")
    print(f"📊 平均起薪: {df_employment['avg_salary'].mean():.2f} 元")
    print(f"📊 博士平均薪资: {df_full[df_full['edu_name'] == '博士']['avg_salary'].mean():.2f} 元")


if __name__ == "__main__":
    generate_full_system_data()