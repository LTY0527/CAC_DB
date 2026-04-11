import io
import logging
import sys
from datetime import datetime

from sqlalchemy import create_engine

from config import DB_URL
from backend.security import bootstrap_security


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

log_file = f"init_security_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("开始初始化系统账号与审计表")
    engine = create_engine(DB_URL, pool_pre_ping=True)
    bootstrap_security(engine)
    logger.info("系统账号与审计表初始化完成")


if __name__ == "__main__":
    main()
