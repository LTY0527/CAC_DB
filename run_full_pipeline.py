"""
数据生产完整流程脚本
整合数据生成、表创建、数据导入三步骤
使用: python run_full_pipeline.py
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# ================================================================
# 日志配置
# ================================================================
log_file = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(script_name, description):
    """
    执行 Python 脚本
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"【步骤】 {description}")
    logger.info(f"{'='*70}")
    
    if not os.path.exists(script_name):
        logger.error(f" 脚本不存在: {script_name}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.getcwd(),
            capture_output=False
        )
        
        if result.returncode == 0:
            logger.info(f"{description} 完成")
            return True
        else:
            logger.error(f"{description} 失败 (返回码: {result.returncode})")
            return False
            
    except Exception as e:
        logger.error(f"{description} 异常: {str(e)}")
        return False

def main():
    """
    执行完整流程
    """
    logger.info("="*70)
    logger.info("数据仓库完整流程执行器")
    logger.info("="*70)
    
    steps = [
        ('platform_data_factory.py', '步骤1生成样本数据'),
        ('create_tables.py', '步骤2初始化数据库表结构'),
        ('PutData.py', '步骤3导入数据到 MySQL'),
    ]
    
    completed = []
    
    for script_name, description in steps:
        if run_command(script_name, description):
            completed.append(description)
        else:
            logger.error(f"流程中止：{description} 失败")
            break
    
    # 显示执行结果
    logger.info("\n" + "="*70)
    logger.info("执行结果汇总")
    logger.info("="*70)
    
    for i, (script_name, description) in enumerate(steps, 1):
        status = "" if description in completed else ""
        logger.info(f"{status} {description}")
    
    logger.info(f"\n成功完成 {len(completed)}/{len(steps)} 个步骤")
    
    if len(completed) == len(steps):
        logger.info("\n 所有步骤执行成功！数据已成功导入 MySQL 数据库")
        return 0
    else:
        logger.warning("\n 部分步骤执行失败，请检查日志")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
