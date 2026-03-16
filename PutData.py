import pandas as pd
import json
from sqlalchemy import create_engine
import os

# 1. 数据库配置
DB_CONFIG = 'mysql+mysqlconnector://root:123456@localhost:3306/bigdata'


def import_all_data():
    """
    执行数据导入流程：
    1. 建立事务连接
    2. 按维度表 -> 事实表的顺序导入
    3. 处理 JSON 字段映射与日期标准化
    """
    try:
        # 创建数据库引擎
        engine = create_engine(DB_CONFIG)

        # 定义导入任务清单（严格遵守外键依赖顺序）
        tasks = [
            {'file': 'dim_student.csv', 'table': 'dim_student'},
            {'file': 'dim_company.csv', 'table': 'dim_company'},
            {'file': 'fact_academic.csv', 'table': 'fact_academic'},
            {'file': 'fact_employment.csv', 'table': 'fact_employment'}
        ]

        # 使用 begin() 开启事务，确保导入过程的原子性（要么全成功，要么全失败）
        with engine.begin() as conn:
            for task in tasks:
                file_path = task['file']
                table_name = task['table']

                if not os.path.exists(file_path):
                    print(f"⚠️ 跳过：未找到文件 {file_path}")
                    continue

                print(f"🚀 正在处理表: {table_name} ...")
                df = pd.read_csv(file_path)

                # --- 特殊逻辑处理 1: 处理 dim_company 的行业字段 ---
                if table_name == 'dim_company':
                    # 将 industry 映射为 strategic_tags 并封装为 JSON 数组
                    if 'industry' in df.columns:
                        df = df.rename(columns={'industry': 'strategic_tags'})

                    # 序列化为 JSON 字符串，确保 MySQL 的 JSON 类型可以识别
                    df['strategic_tags'] = df['strategic_tags'].apply(
                        lambda x: json.dumps([x], ensure_ascii=False) if pd.notnull(x) else "[]"
                    )

                # --- 特殊逻辑处理 2: 标准化 fact_employment 的日期 ---
                if table_name == 'fact_employment':
                    # 强制转换为 datetime 对象，解决 CSV 字符串与 MySQL DATE 类型的匹配问题
                    df['first_insured_date'] = pd.to_datetime(df['first_insured_date']).dt.date

                # --- 批量写入数据库 ---
                # method='multi' 显著提升 5W 条数据的写入效率
                df.to_sql(
                    name=table_name,
                    con=conn,
                    if_exists='append',  # 若表已有数据则追加
                    index=False,
                    method='multi',
                    chunksize=5000  # 每批次处理 5000 条，平衡内存占用与速度
                )
                print(f"✅ {table_name} 导入成功，共 {len(df)} 条记录")

        print("\n🏆 数据仓库同步任务已圆满完成。")

    except Exception as e:
        print(f"🚨 导入过程发生致命错误：\n{str(e)}")


if __name__ == "__main__":
    import_all_data()