import os
import logging
from typing import Dict, Any

# 生产环境数据库配置
PRODUCTION_DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_DATABASE', 'factor_platform'),
    'charset': 'utf8mb4',
    'autocommit': True,
    'connect_timeout': 30,
    'read_timeout': 30,
    'write_timeout': 30,
}

# 测试环境数据库配置
TEST_DB_CONFIG = {
    'host': os.getenv('TEST_DB_HOST', '192.168.1.174'),
    'port': int(os.getenv('TEST_DB_PORT', 33308)),
    'user': os.getenv('TEST_DB_USER', 'root'),
    'password': os.getenv('TEST_DB_PASSWORD', 'Deepwin2025!@'),
    'database': os.getenv('TEST_DB_DATABASE', 'Factor_system'),
    'charset': 'utf8mb4',
    'autocommit': True,
    'connect_timeout': 30,
    'read_timeout': 30,
    'write_timeout': 30,
}

# =================================================================
# 数据库表名
# =================================================================

FACTOR_INFO_TABLE_NAME = {
    'factor_info': 'factor_info',
    'factor_result': 'factor_result'
}

# =================================================================
# 连接池配置
# =================================================================

CONNECTION_POOL_CONFIG = {
    'pool_name': 'factor_platform_pool',
    'pool_size': int(os.getenv('DB_POOL_SIZE', 20)),          # 连接池大小
    'pool_reset_session': True,                               # 重置会话
    'pool_pre_ping': True,                                    # 连接前ping检查
    'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 30)),    # 最大溢出连接数
    'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),  # 连接回收时间(秒)
}

# =================================================================
# 重试配置
# =================================================================

RETRY_CONFIG = {
    'max_retries': int(os.getenv('DB_MAX_RETRIES', 3)),       # 最大重试次数
    'retry_delay': float(os.getenv('DB_RETRY_DELAY', 1.0)),   # 重试延迟(秒)
    'backoff_factor': float(os.getenv('DB_BACKOFF_FACTOR', 2.0)),  # 退避因子
}

# =================================================================
# 日志配置
# =================================================================

LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'sql_debug': os.getenv('SQL_DEBUG', 'False').lower() == 'true',
}


def get_environment() -> str:
    """获取当前运行环境"""
    return os.getenv('ENVIRONMENT', 'test')


def is_test_environment() -> bool:
    """判断是否为测试环境"""
    return get_environment().lower() in ['test', 'testing']


def get_db_config() -> Dict[str, Any]:
    """根据环境获取数据库配置"""
    if is_test_environment():
        return TEST_DB_CONFIG.copy()
    else:
        return PRODUCTION_DB_CONFIG.copy()


def factor_logger(file_name: str = os.path.basename(__name__)):
    """日志实例"""
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG['level']),
        format=LOGGING_CONFIG['format']
    )
    return logging.getLogger(file_name)
