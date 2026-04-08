import os
import sys
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat, lit, when

from config import DB_SETTINGS, JAR_PATH, jdbc_url


BASE_DIR = Path(__file__).resolve().parent
HADOOP_HOME = Path(os.environ.get("HADOOP_HOME", r"D:\hadoop"))
TXT_IC = "\u96c6\u6210\u7535\u8def"
TXT_AI = "\u4eba\u5de5\u667a\u80fd"
TXT_BIO = "\u751f\u7269\u533b\u836f"
TXT_FINANCE = "\u73b0\u4ee3\u91d1\u878d"
TXT_SMART_MFG = "\u667a\u80fd\u5236\u9020"
TXT_BUILDING = "\u5efa\u7b51"
TXT_EDU = "\u6559\u80b2"
TXT_CULTURE = "\u6587\u5316"
TXT_BUILDING_ENG = "\u5efa\u7b51\u5de5\u7a0b"
TXT_EDU_RESEARCH = "\u6559\u80b2\u79d1\u7814"
TXT_MEDIA = "\u6587\u5316\u4f20\u5a92"
TXT_NORMAL_INDUSTRY = "\u5e38\u89c4\u884c\u4e1a"
TXT_FEATURED_MAJOR = "\u7279\u8272\u4e13\u4e1a"
TXT_GENERAL_MAJOR = "\u901a\u7528\u4e13\u4e1a"

if HADOOP_HOME.exists():
    os.environ["HADOOP_HOME"] = str(HADOOP_HOME)
    os.environ["hadoop.home.dir"] = str(HADOOP_HOME)
    os.environ["PATH"] = str(HADOOP_HOME / "bin") + os.pathsep + os.environ["PATH"]

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable


DB_PROPERTIES = {
    "user": DB_SETTINGS["user"],
    "password": DB_SETTINGS["password"],
    "driver": DB_SETTINGS["driver"],
}


def create_spark_session(app_name: str) -> SparkSession:
    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.adaptive.enabled", "true")
    )

    jar_path = Path(JAR_PATH)
    if jar_path.exists():
        builder = (
            builder.config("spark.jars", str(jar_path))
            .config("spark.driver.extraClassPath", str(jar_path))
            .config("spark.executor.extraClassPath", str(jar_path))
        )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def _load_tables_from_jdbc(spark: SparkSession):
    student = spark.read.jdbc(url=jdbc_url, table="dim_student", properties=DB_PROPERTIES).alias("s")
    academic = spark.read.jdbc(url=jdbc_url, table="fact_academic", properties=DB_PROPERTIES).alias("a")
    employment = spark.read.jdbc(url=jdbc_url, table="fact_employment", properties=DB_PROPERTIES).alias("e")
    company = spark.read.jdbc(url=jdbc_url, table="dim_company", properties=DB_PROPERTIES).alias("c")
    return student, academic, employment, company


def _load_tables_from_csv(spark: SparkSession):
    student = spark.read.option("header", True).option("inferSchema", True).csv(str(BASE_DIR / "dim_student.csv")).alias("s")
    academic = spark.read.option("header", True).option("inferSchema", True).csv(str(BASE_DIR / "fact_academic.csv")).alias("a")
    employment = spark.read.option("header", True).option("inferSchema", True).csv(str(BASE_DIR / "fact_employment.csv")).alias("e")
    company = spark.read.option("header", True).option("inferSchema", True).csv(str(BASE_DIR / "dim_company.csv")).alias("c")
    return student, academic, employment, company


def _load_tables(spark: SparkSession):
    preferred_source = os.environ.get("MATCHING_DATA_SOURCE", "csv").lower()

    if preferred_source == "csv":
        return _load_tables_from_csv(spark)

    try:
        return _load_tables_from_jdbc(spark)
    except Exception as exc:
        print(f"[Spark] JDBC \u8bfb\u53d6\u5931\u8d25\uff0c\u81ea\u52a8\u56de\u9000\u5230\u672c\u5730 CSV: {exc}")
        return _load_tables_from_csv(spark)


def load_joined_dataset(spark: SparkSession):
    s, a, e, c = _load_tables(spark)

    joined = s.join(a, col("s.student_id") == col("a.student_id"), "inner").join(
        e, col("s.student_id") == col("e.student_id"), "inner"
    )

    if "company_id" in e.columns and "company_id" in c.columns:
        joined = joined.join(c, col("e.company_id") == col("c.company_id"), "left")
    else:
        joined = joined.join(c, col("e.employer_name") == col("c.employer_name"), "left")

    industry_expr = (
        when(col("c.strategic_tags").contains(TXT_IC), lit(TXT_IC))
        .when(col("c.strategic_tags").contains(TXT_AI), lit(TXT_AI))
        .when(col("c.strategic_tags").contains(TXT_BIO), lit(TXT_BIO))
        .when(col("c.strategic_tags").contains(TXT_FINANCE), lit(TXT_FINANCE))
        .when(col("c.strategic_tags").contains(TXT_SMART_MFG), lit(TXT_SMART_MFG))
        .when(col("c.strategic_tags").contains(TXT_BUILDING), lit(TXT_BUILDING_ENG))
        .when(col("c.strategic_tags").contains(TXT_EDU), lit(TXT_EDU_RESEARCH))
        .when(col("c.strategic_tags").contains(TXT_CULTURE), lit(TXT_MEDIA))
        .otherwise(lit(TXT_NORMAL_INDUSTRY))
    )

    major_tag_expr = when(
        col("s.school_name").isin(
            "复旦大学",
            "上海交通大学",
            "同济大学",
            "华东师范大学",
            "上海财经大学",
            "东华大学",
            "华东理工大学",
        )
        & col("a.major_name").isin(
            "临床医学",
            "基础医学",
            "数学与应用数学",
            "金融学",
            "新闻学",
            "计算机科学与技术",
            "软件工程",
            "机械工程",
            "电子信息工程",
            "土木工程",
            "建筑学",
            "城乡规划",
            "交通工程",
            "环境工程",
            "教育学",
            "小学教育",
            "心理学",
            "统计学",
            "金融工程",
            "会计学",
            "财务管理",
            "纺织工程",
            "服装设计与工程",
            "轻化工程",
            "化学工程与工艺",
            "制药工程",
            "应用化学",
            "信息管理与信息系统",
        ),
        lit(TXT_FEATURED_MAJOR),
    ).otherwise(lit(TXT_GENERAL_MAJOR))

    base_df = joined.select(
        col("s.student_id").alias("student_id"),
        col("s.student_name").alias("student_name"),
        col("s.origin_place").alias("origin_place"),
        col("s.school_name").alias("school_name"),
        col("s.school_level").alias("school_level"),
        col("s.edu_name").alias("edu_name"),
        col("a.discipline_category").alias("discipline_category"),
        col("a.major_name").alias("major_name"),
        col("a.major_category").alias("major_category"),
        col("a.skill_level").alias("skill_level"),
        col("e.employer_name").alias("employer_name"),
        col("e.avg_salary").cast("double").alias("avg_salary"),
        col("e.leading_industry_tag").alias("leading_industry_tag"),
        col("c.company_scale").alias("company_scale"),
        industry_expr.alias("industry_type"),
        major_tag_expr.alias("major_type"),
    )

    labeled_df = (
        base_df.withColumn("school_name_tag", concat(lit("\u9662\u6821:"), col("school_name")))
        .withColumn("school_level_tag", concat(lit("\u9662\u6821\u5c42\u6b21:"), col("school_level")))
        .withColumn("discipline_tag", concat(lit("\u5b66\u79d1:"), col("discipline_category")))
        .withColumn("major_tag", concat(lit("\u4e13\u4e1a:"), col("major_name")))
        .withColumn("major_type_tag", concat(lit("\u4e13\u4e1a\u7c7b\u578b:"), col("major_type")))
        .withColumn("skill_tag", concat(lit("\u6280\u80fd:"), col("skill_level")))
        .withColumn("industry_tag", concat(lit("\u884c\u4e1a:"), col("industry_type")))
        .withColumn("company_scale_tag", concat(lit("\u4f01\u4e1a\u89c4\u6a21:"), col("company_scale")))
        .withColumn("leading_industry_label", concat(lit("\u4ea7\u4e1a\u6807\u7b7e:"), col("leading_industry_tag")))
    )
    return labeled_df
