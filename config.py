# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from urllib.parse import quote_plus

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if load_dotenv:
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

JAR_PATH = os.path.join(BASE_DIR, "libs", "mysql-connector-java-8.0.11.jar")

DB_SETTINGS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "bigdata"),
    "charset": os.getenv("DB_CHARSET", "utf8mb4"),
    "driver": os.getenv("DB_JDBC_DRIVER", "com.mysql.cj.jdbc.Driver"),
}


def build_sqlalchemy_url(driver: str = "mysqlconnector") -> str:
    encoded_password = quote_plus(DB_SETTINGS["password"])
    base_url = (
        f"mysql+{driver}://{DB_SETTINGS['user']}:{encoded_password}"
        f"@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"
    )
    if driver == "pymysql":
        return f"{base_url}?charset={DB_SETTINGS['charset']}"
    return base_url


DB_URL = build_sqlalchemy_url("mysqlconnector")
DB_URL_PYMYSQL = build_sqlalchemy_url("pymysql")

jdbc_url = (
    f"jdbc:mysql://{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"
    "?serverTimezone=Asia/Shanghai&useSSL=false&allowPublicKeyRetrieval=true"
)

SPARK_CONFIG = {
    "app_name": "CAC_DB_Integrated_Platform",
    "master": "local[*]",
    "hdfs_path": "hdfs://localhost:9000/user/data/",
    "jar_path": JAR_PATH,
}

KPI_TARGETS = {
    "matching_rate_improvement": 0.325,
    "mismatch_rate_reduction": 0.15,
    "data_accuracy_min": 0.995,
    "latency_max_seconds": 2,
}
