"""
MySQL 数据库基础服务类
提供数据库连接、配置获取、表名验证等基础功能
"""
import threading
from typing import Dict, Optional, Any
import pymysql
import pymysql.cursors
from ..base_service import BaseService

# 表名白名单，防止 SQL 注入
TABLE_WHITELIST = {
    'users', 'assets', 'works', 'chapters',
    'user_oauth_accounts', 'token_blacklist', 'oauth_states'
}


class MySQLBaseService(BaseService):
    """
    MySQL 基础服务类（单例）
    提供数据库连接管理、配置获取、基础表操作
    """

    _instance = None
    _lock = threading.Lock()
    _connection = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    # ---------- 初始化 ----------
    def init_app(self, app):
        """Flask 应用初始化时调用"""
        with app.app_context():
            self._initialize()

    def _initialize(self):
        """初始化数据库连接"""
        if self._initialized:
            return

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
                autocommit=False
            )
            self._initialized = True
            self._log("MySQL service initialized successfully")
        except Exception as e:
            self._log(f"Error initializing MySQL service: {e}", level='error')
            raise

    def _get_mysql_config(self) -> Dict[str, Any]:
        """从 Flask 配置或环境变量获取 MySQL 配置"""
        return {
            'host': self._get_config('MYSQL_HOST', 'localhost'),
            'port': int(self._get_config('MYSQL_PORT', 3306)),
            'user': self._get_config('MYSQL_USER', 'root'),
            'password': self._get_config('MYSQL_PASSWORD', ''),
            'database': self._get_config('MYSQL_DB', 'narloom'),
            'charset': self._get_config('MYSQL_CHARSET', 'utf8mb4')
        }

    def _validate_table_name(self, table_name: str) -> str:
        """验证表名是否在白名单中"""
        if table_name not in TABLE_WHITELIST:
            raise ValueError(f"Invalid table name: {table_name}")
        return table_name

    def _ensure_connection(self):
        """确保连接有效，若断开则重连"""
        if not self._connection:
            self._initialize()
        try:
            self._connection.ping(reconnect=True)
        except Exception:
            self._initialize()
        return self._connection

    def _create_tables_if_not_exists(self):
        """创建所有必要的表（如果不存在）"""
        conn = self._connection
        try:
            with conn.cursor() as cursor:
                # 创建 users 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id VARCHAR(100) PRIMARY KEY,
                        email VARCHAR(255) UNIQUE COMMENT '用户邮箱（OAuth 用户可为空）',
                        password_hash VARCHAR(255) COMMENT '密码哈希（OAuth 用户可为空）',
                        name VARCHAR(255) DEFAULT '',
                        bio TEXT,
                        phone VARCHAR(20) NULL COMMENT '手机号',
                        avatar_url VARCHAR(500) NULL COMMENT '头像 URL',
                        last_login_at DATETIME NULL COMMENT '最后登录时间',
                        last_login_provider VARCHAR(20) NULL COMMENT '最后登录方式（email/wechat/qq）',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        INDEX idx_email (email),
                        INDEX idx_last_login_provider (last_login_provider)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """)

                # 创建 user_oauth_accounts 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_oauth_accounts (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(100) NOT NULL COMMENT '关联的用户 ID',
                        provider VARCHAR(20) NOT NULL COMMENT '提供商：wechat, qq',
                        open_id VARCHAR(100) NOT NULL COMMENT '用户在提供商的唯一 ID',
                        union_id VARCHAR(100) NULL COMMENT '统一 ID（微信生态下跨应用唯一）',
                        access_token TEXT NULL COMMENT 'OAuth 访问令牌',
                        access_token_expires_at DATETIME NULL COMMENT '令牌过期时间',
                        refresh_token TEXT NULL COMMENT 'OAuth 刷新令牌',
                        provider_data JSON NULL COMMENT '原始用户数据（昵称、头像等）',
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        UNIQUE KEY unique_provider_open_id (provider, open_id),
                        UNIQUE KEY unique_provider_union_id (provider, union_id),
                        INDEX idx_user_id (user_id),
                        INDEX idx_provider (provider),
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """)

                # 创建 assets 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS assets (
                        asset_id VARCHAR(100) PRIMARY KEY,
                        user_id VARCHAR(100) NOT NULL,
                        work_id VARCHAR(100),
                        asset_type VARCHAR(50) NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        INDEX idx_user_id (user_id),
                        INDEX idx_work_id (work_id),
                        INDEX idx_asset_type (asset_type)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """)

                # 创建 works 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS works (
                        work_id VARCHAR(100) PRIMARY KEY,
                        author_id VARCHAR(100) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        genre VARCHAR(100) DEFAULT '',
                        tags TEXT,
                        status VARCHAR(50) DEFAULT 'draft',
                        chapter_count INT DEFAULT 0,
                        word_count INT DEFAULT 0,
                        description TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        INDEX idx_author_id (author_id),
                        INDEX idx_status (status)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """)

                # 创建 chapters 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chapters (
                        chapter_id VARCHAR(100) PRIMARY KEY,
                        work_id VARCHAR(100) NOT NULL,
                        author_id VARCHAR(100) NOT NULL,
                        chapter_num INT NOT NULL,
                        chapter_title VARCHAR(255) DEFAULT '',
                        content TEXT,
                        status VARCHAR(50) DEFAULT 'draft',
                        word_count INT DEFAULT 0,
                        notes TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        INDEX idx_work_id (work_id),
                        INDEX idx_author_id (author_id),
                        INDEX idx_chapter_num (work_id, chapter_num)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """)

                # 创建 token_blacklist 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS token_blacklist (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        jti VARCHAR(100) NOT NULL UNIQUE COMMENT 'JWT ID（唯一标识）',
                        user_id VARCHAR(100) NULL COMMENT '用户 ID',
                        token_type VARCHAR(20) NOT NULL DEFAULT 'access' COMMENT '令牌类型（access/refresh）',
                        blacklisted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '加入黑名单时间',
                        expires_at DATETIME NOT NULL COMMENT '令牌原始过期时间',
                        reason VARCHAR(50) DEFAULT 'logout' COMMENT '加入黑名单原因（logout/revoke/ban）',
                        INDEX idx_jti (jti),
                        INDEX idx_user_id (user_id),
                        INDEX idx_expires_at (expires_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """)

                # 创建 oauth_states 表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS oauth_states (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        state VARCHAR(100) NOT NULL UNIQUE COMMENT '随机生成的 state 参数',
                        user_id VARCHAR(100) NULL COMMENT '关联的用户 ID（如已登录绑定场景）',
                        provider VARCHAR(20) NOT NULL COMMENT 'OAuth 提供商',
                        action VARCHAR(20) DEFAULT 'login' COMMENT '操作类型（login/bind）',
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME NOT NULL COMMENT '过期时间（10 分钟）',
                        consumed_at DATETIME NULL COMMENT '消耗时间',
                        consumed_by_action VARCHAR(20) NULL COMMENT '被用于哪个 action',
                        INDEX idx_state (state),
                        INDEX idx_expires_at (expires_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                """)

                conn.commit()
                self._log("All required tables ensured with indexes")
        except Exception as e:
            self._log(f"Error creating tables: {e}", level='error')
            pass


mysql_base_service = MySQLBaseService()
