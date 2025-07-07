import os
import threading
import time
import json
import logging
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager

from env import (
    get_db_config,
    RETRY_CONFIG,
    factor_logger,
    FACTOR_INFO_TABLE_NAME
)


class DatabaseConnectionManager:
    """
    数据库连接管理器 - 单例模式
    提供连接池、重试机制和线程安全的数据库访问
    """

    _instance = None
    _lock = threading.Lock()
    _local = threading.local()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.db_config = get_db_config()
        self.retry_config = RETRY_CONFIG
        self._initialized = True
        self.logging = factor_logger(self.__class__.__name__)
        self.logging.info("DatabaseConnectionManager initialized")

    def get_connection(self) -> pymysql.Connection:
        """获取数据库连接，支持连接池和重试机制"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = self._create_connection_with_retry()

        # 检查连接是否有效
        try:
            self._local.connection.ping(reconnect=True)
        except Exception as e:
            self.logging.warning(f"Connection ping failed, recreating: {e}")
            self._local.connection = self._create_connection_with_retry()

        return self._local.connection

    def _create_connection_with_retry(self) -> pymysql.Connection:
        """创建数据库连接，带重试机制"""
        last_exception = None

        for attempt in range(self.retry_config['max_retries']):
            try:
                # 创建连接配置副本，避免参数冲突
                conn_config = self.db_config.copy()
                conn_config['autocommit'] = False  # 手动管理事务
                conn_config['cursorclass'] = DictCursor

                connection = pymysql.connect(**conn_config)
                self.logging.info(f"Database connection created successfully")
                return connection

            except Exception as e:
                last_exception = e
                wait_time = self.retry_config['retry_delay'] * (
                        self.retry_config['backoff_factor'] ** attempt
                )

                self.logging.warning(
                    f"Database connection attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {wait_time} seconds..."
                )

                if attempt < self.retry_config['max_retries'] - 1:
                    time.sleep(wait_time)

        raise ConnectionError(
            f"Failed to connect to database after {self.retry_config['max_retries']} attempts. "
            f"Last error: {last_exception}"
        )

    def close_connection(self):
        """关闭当前线程的数据库连接"""
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                self._local.connection.close()
                self.logging.info("Database connection closed")
            except Exception as e:
                self.logging.error(f"Error closing database connection: {e}")
            finally:
                self._local.connection = None


class GetFactorDataAPI:
    """从数据库中获取因子数据接口"""

    def __init__(self):
        self.db_manager = DatabaseConnectionManager()
        self.logging = factor_logger(self.__class__.__name__)

    def _get_connection(self):
        """获取数据库连接"""
        return self.db_manager.get_connection()

    @contextmanager
    def transaction(self):
        conn = self._get_connection()
        try:
            conn.begin()  # 开启事务
            yield conn
            conn.commit()  # 提交事务
            self.logging.debug("Transaction committed successfully")
        except Exception as e:
            conn.rollback()  # 事务回滚
            self.logging.error(f"Transaction rolled back due to error: {e}")
            raise

    def _analysis_input_dict(self, factor_info: dict):
        """解析参数内容"""
        if type(factor_info) is not dict:
            self.logging.error("传递参数不符合要求")
            raise TypeError(f"factor_info 参数类型错误，期望是 dict，实际是 {type(factor_info).__name__}")
        try:
            self.factor_name = factor_info['factor_name']  # 因子名称
            self.version = factor_info['version']  # 因子版本
            self.factor_type = factor_info['factor_type']  # 因子类型
            self.submitted_by = factor_info['submitted_by']  # 因子提交人
        except Exception as e:
            self.logging.error("缺失必填参数类型, factor_name, version, factor_type, submitted_by")
            raise ValueError("缺失必填参数")
        self.factor_args = factor_info.get('factor_args', {})
        self.factor_status = '0'
        self.review_by = factor_info.get('review_by', 'http://feishudizhi.com')
        self.review_notes = factor_info.get('review_notes', None)

    def create_factor_info(self, factor_info: dict):
        """提交因子信息"""
        self._analysis_input_dict(factor_info)
        with self.transaction() as conn:
            try:
                sql = f"""
                    INSERT INTO {FACTOR_INFO_TABLE_NAME.get('factor_info')} (
                        factor_name, version, factor_args, factor_type, factor_status,
                        submitted_by, review_by, review_notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    self.factor_name,
                    self.version,
                    json.dumps(self.factor_args),  # 转换为字符串存储
                    self.factor_type,
                    self.factor_status,
                    self.submitted_by,
                    self.review_by,
                    self.review_notes
                )
                conn.cursor().execute(sql, params)
                self.logging.info(f"因子: {self.factor_name} 版本: {self.version} 入库成功")
            except Exception as e:
                if "1062" in str(e):
                    self.logging.warning(f"因子: {self.factor_name} 版本: {self.version} 存在库中")
                    return
                self.logging.error(f"因子: {self.factor_name} 版本: {self.version} 入库失败， {e}")
                raise

    def update_factor_status(self, factor_name: str, factor_version: str):
        """审批因子"""
        if not self.factor_exists(factor_name, factor_version):
            self.logging.warning(f"审批 {factor_name}因子 {factor_version}版本 不存在，请先提交")
            return
        if len(self.get_factor_pending_status(factor_name, factor_version)) == 0:
            self.logging.warning(f"审批 {factor_name}因子 {factor_version}版本 已经通过审批")
            return
        """TODO: 需要插入一个函数，审核这个因子是否通过，返回 字符串1，通过。字符串2，不通过"""
        with self.transaction() as conn:
            try:
                sql = f"""
                    UPDATE {FACTOR_INFO_TABLE_NAME.get('factor_info')} SET `factor_status` = %s
                        WHERE `factor_name` = %s AND `version` = %s
                """
                params = ('1', factor_name, factor_version)
                cursor = conn.cursor()
                cursor.execute(sql, params)
                self.logging.info(f"因子 {factor_name} 版本 {factor_version} 通过审批")
            except Exception as e:
                self.logging.error(f"函数 {self.update_factor_status.__name__} 审批因子失败, {e}")
                raise

    def get_all_factor_version(self, factor_name):
        """获取因子所有版本"""
        with self.transaction() as conn:
            try:
                sql = f"SELECT version FROM {FACTOR_INFO_TABLE_NAME.get('factor_info')} WHERE `factor_name` = %s"
                cursor = conn.cursor()
                cursor.execute(sql, [factor_name,])
                results = cursor.fetchall()
                return results
            except Exception as e:
                raise

    def get_all_factor_name(self):
        """获取所有因子名称"""
        with self.transaction() as conn:
            try:
                sql = f"SELECT DISTINCT factor_name FROM {FACTOR_INFO_TABLE_NAME.get('factor_info')}"
                cursor = conn.cursor()
                cursor.execute(sql)
                return cursor.fetchall()
            except Exception as e:
                raise

    def get_new_factor_name(self, factor_name: str):
        """获取因子的最新版本"""
        if not self.factor_exists(factor_name):
            self.logging.warning(f"{factor_name} 因子不存在")
            return
        with self.transaction() as conn:
            try:
                sql = f"""
                    SELECT version FROM {FACTOR_INFO_TABLE_NAME.get('factor_info')} WHERE `factor_name` = %s
                        AND `factor_status` = '1' AND `updated_at` = (
                            SELECT MAX(updated_at) FROM {FACTOR_INFO_TABLE_NAME.get('factor_info')} 
                            WHERE `factor_name` = %s AND `factor_status` = '1'
                        )
                """
                params = (factor_name, factor_name)
                cursor = conn.cursor()
                cursor.execute(sql, params)
                result = cursor.fetchone()
                return result
            except Exception as e:
                raise

    def get_factor_pending_status(self, factor_name: str = None, factor_version: str = None):
        """获取处于审核状态的因子"""
        with self.transaction() as conn:
            try:
                # 基础查询
                sql = f"SELECT * FROM {FACTOR_INFO_TABLE_NAME.get('factor_info')} WHERE `factor_status` = %s"
                params = ['0']  # 用于存储 SQL 参数

                # 添加条件
                if factor_name is not None:
                    sql += " AND `factor_name` = %s"
                    params.append(factor_name)

                if factor_version is not None:
                    sql += " AND `version` = %s"
                    params.append(factor_version)

                cursor = conn.cursor()
                cursor.execute(sql, params)
                results = cursor.fetchall()
                return results
            except Exception as e:
                self.logging.error(f"函数 {self.get_factor_pending_status.__name__}内 获取审核因子失败，{e}")
                raise

    def factor_exists(self, factor_name: str, factor_version: str = None):
        """判断因子，以及对应的版本是否存在"""
        with self.transaction() as conn:
            try:
                sql = f"SELECT * FROM {FACTOR_INFO_TABLE_NAME.get('factor_info')} WHERE `factor_name` = %s"
                params = [factor_name]
                if factor_version is not None:
                    sql += " AND `version` = %s"
                    params.append(factor_version)
                cursor = conn.cursor()
                cursor.execute(sql, params)
                results = cursor.fetchall()
                if results:
                    return True
                return False
            except Exception as e:
                self.logging.error(f"函数{self.factor_exists.__name__} 内 获取指定因子失败， {e}")
                raise

    def write_node_factor_data(self, factor_name: str, factor_version: str,
                               code: str, day: str, data_type: str, save_path: str = './save_path',
                               data_status: str = 1, extra_info: dict = None
                               ):
        """将计算因子结果信息保存到数据库中"""
        with self.transaction() as conn:
            try:
                sql = f"""
                    INSERT INTO {FACTOR_INFO_TABLE_NAME.get('factor_result')} (
                        factor_name, version, code, data_type, factor_path,
                        calculated_date, data_status, extra_info
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    factor_name,
                    factor_version,
                    code,
                    data_type,
                    save_path,
                    day,
                    data_status,
                    json.dumps(extra_info)
                )
                conn.cursor().execute(sql, params)
                self.logging.info(f"{factor_name}因子 {factor_version} 版本计算{code} {day}结果入库成功")
            except Exception as e:
                self.logging.error(f"{factor_name}因子 {factor_version} 版本计算{code} {day}结果入库失败: {e}")
                raise

    def exists_source_code_data(self, factor_name: str, factor_version: str,
                                code: str, day: str):
        """判定因子结果存在"""
        with self.transaction() as conn:
            try:
                sql = f"""
                    SELECT * FROM {FACTOR_INFO_TABLE_NAME.get('factor_result')} WHERE `factor_name` = %s
                    AND `version` = %s AND `code` = %s AND `calculated_date` = %s
                """
                params = (factor_name, factor_version, code, day)
                cursor = conn.cursor()
                cursor.execute(sql, params)
                results = cursor.fetchall()

                if results:
                    return True
                return False
            except Exception as e:
                self.logging.error(f"{e}")
                raise

    def close(self):
        self.db_manager.close_connection()
