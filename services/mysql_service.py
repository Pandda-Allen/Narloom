import os
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from flask import current_app
import pymysql
import pymysql.cursors

class MySQLService:
    """MySQL 服务类，提供数据库连接和基本操作"""

    _instance = None
    _connection = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    # ---------- 初始化 ----------
    def init_app(self, app):
        with app.app_context():
            self._initialize()
    

    def _initialize(self):
        if self._initialized:
            return
        
        # 获取配置
        config = self._get_mysql_config()
        if not all(config.values()):
            self._log("MySQL configuration incomplete", level='error')
            raise RuntimeError("MySQL configuration incomplete")
        
        try:
            self._connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                charset=config['charset'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False # 手动控制事务
            )
            self._initialized = True
            self._log("MySQL service initialized successfully")
        except Exception as e:
            self._log(f"Error initializing MySQL service: {e}", level='error')
            raise
    
    def _get_mysql_config(self) -> dict:
        """从 Flask 配置或环境变量获取 MySQL 配置"""
        return {
            'host': self._get_config('MYSQL_HOST', 'localhost'),
            'port': int(self._get_config('MYSQL_PORT', 3306)),
            'user': self._get_config('MYSQL_USER', 'root'),
            'password': self._get_config('MYSQL_PASSWORD', ''),
            'database': self._get_config('MYSQL_DB', 'narloom_db'),
            'charset': self._get_config('MYSQL_CHARSET', 'utf8mb4')
        }

    def _get_config(self, key: str, default: None) -> Optional[str]:
        """从 Flask 配置或环境变量获取配置值"""
        try:
            if current_app:
                value = current_app.config.get(key, default)
                if value is not None:
                    return value
        except RuntimeError:
            pass
        return os.getenv(key, default)
    
    def _log(self, message: str, level: str = 'info') -> None:
        """记录日志"""
        try:
            if current_app:
                logger = current_app.logger
                getattr(logger, level)(message)
                return
        except (RuntimeError, AttributeError):
            pass
        logging.basicConfig(level=logging.INFO)
        getattr(logging, level)(message)

    # ---------------- 链接保证 ----------------
    def _ensure_connection(self):
        """确保连接有效，若断开则重连"""
        if not self._connection:
            self._initialize()
        try:
            self._connection.ping(reconnect=True)
        except Exception:
            self._initialize()
        return self._connection
    
    # ---------------- 资产操作 ----------------
    def insert_asset(self, user_id: str, asset_type:str, work_id: str = None) -> Dict:
        """
        插入资产(asset)记录到MySQL数据库
        :return: 插入的行数据(包含 asset_id, created_at, updated_at)
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_ASSETS', 'assets')
        asset_id = str(uuid.uuid4())
        now = datetime.now()

        with conn.cursor() as cursor:
            sql = f"""
                INSERT INTO {table} (asset_id, user_id, work_id, asset_type, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (asset_id, user_id, work_id, asset_type, now, now))
            conn.commit()

        return {
            'asset_id': asset_id,
            'user_id': user_id,
            'asset_type': asset_type,
            'work_id': work_id,
            'created_at': now.strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': now.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def update_asset(self, asset_id: str, update_data: Data) -> Optional[Dict]:
        """
        更新资产(asset)记录到MySQL数据库(仅允许更新work_id, asset_type)
        :param: update_data: 可包含'work_id', 'asset_type'的字典
        :return: 更新后的完整行数据，若资产不存在返回 None
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_ASSETS', 'assets')
        now = datetime.now()

        # 构建 SET 语句
        set_clauses = []
        params = []
        if 'work_id' in update_data:
            set_clauses.append("work_id = %s")
            params.append(update_data['work_id'])
        if 'asset_type' in update_data:
            set_clauses.append("asset_type = %s")
            params.append(update_data['asset_type'])
        
        if not set_clauses:
            # 没有要更新的字段，但仍需更新时间戳
            set_clauses.append("updated_at = %s")
            params.append(now)
        else:
            set_clauses.append("updated_at = %s")
            params.append(now)
        
        params.append(asset_id)

        with conn.cursor() as cursor:
            # 先检查资产是否存在
            cursor.execute(f"SELECT asset_id FROM {table} WHERE asset_id = %s", (asset_id,))
            if not cursor.fetchone():
                return None
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE asset_id = %s"
            cursor.execute(sql, params)
            conn.commit()

            # 返回更新后的完整行数据
            cursor.execute(f"SELECT * FROM {table} WHERE asset_id = %s", (asset_id,))
            return cursor.fetchone()
    
    def delete_asset(self, asset_id: str) -> bool:
        """
        删除资产(asset)记录从MySQL数据库
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_ASSETS', 'assets')

        with conn.cursor() as cursor:
            sql = f"DELETE FROM {table} WHERE asset_id = %s"
            cursor.execute(sql, (asset_id,))
            conn.commit()
            return cursor.rowcount > 0
        
    def fetch_asset_by_id(self, asset_id: str) -> Optional[Dict]:
        """
        根据 asset_id 从MySQL数据库获取资产(asset)记录
        :return: 资产记录字典，若不存在返回 None
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_ASSETS', 'assets')

        with conn.cursor() as cursor:
            sql = f"SELECT * FROM {table} WHERE asset_id = %s"
            cursor.execute(sql, (asset_id,))
            return cursor.fetchone()
        
    def fetch_assets(self, user_id: str, asset_type: Optional[str] = None, work_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        根据条件从MySQL数据库获取资产(asset)记录列表
        :return: 资产记录字典列表
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_ASSETS', 'assets')
        conditions = ["user_id = %s"]
        params = [user_id]

        if asset_type:
            conditions.append("asset_type = %s")
            params.append(asset_type)        
        if work_id:
            conditions.append("work_id = %s")
            params.append(work_id)

        sql = f"SELECT * FROM {table} WHERE {' AND '.join(conditions)} ORDER BY updated_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
        
mysql_service = MySQLService()