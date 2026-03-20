"""
MySQL 服务类，提供数据库连接和基本操作。
使用单例模式，线程安全。
"""
import uuid
import json
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List
import pymysql
import pymysql.cursors
from .base_service import BaseService

# 表名白名单，防止 SQL 注入
TABLE_WHITELIST = {
    'users', 'assets', 'works', 'chapters', 'user_oauth_accounts', 'token_blacklist', 'oauth_states'
}

class MySQLService(BaseService):
    """MySQL 服务类，提供数据库连接和基本操作"""

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
                autocommit=False
            )
            # 确保 users 表存在
            self._create_users_table_if_not_exists()
            self._create_tables_if_not_exists()
            self._initialized = True
            self._log("MySQL service initialized successfully")
        except Exception as e:
            self._log(f"Error initializing MySQL service: {e}", level='error')
            raise

    def _validate_table_name(self, table_name: str) -> str:
        """验证表名是否在白名单中"""
        if table_name not in TABLE_WHITELIST:
            raise ValueError(f"Invalid table name: {table_name}")
        return table_name

    def _create_users_table_if_not_exists(self):
        """创建 users 表（如果不存在）"""
        conn = self._connection
        table = 'users'
        try:
            with conn.cursor() as cursor:
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

                # 创建 user_oauth_accounts 表（如果不存在）
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

                conn.commit()
                self._log("Table 'users' and 'user_oauth_accounts' ensured")
        except Exception as e:
            self._log(f"Error creating users table: {e}", level='error')
            pass

    def _create_tables_if_not_exists(self):
        """创建所有必要的表（如果不存在）"""
        conn = self._connection
        try:
            with conn.cursor() as cursor:
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

                # 创建 token_blacklist 表（JWT 令牌黑名单）
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

                # 创建 oauth_states 表（OAuth CSRF 防护）
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

    def _get_mysql_config(self) -> dict:
        """从 Flask 配置或环境变量获取 MySQL 配置"""
        return {
            'host': self._get_config('MYSQL_HOST', 'localhost'),
            'port': int(self._get_config('MYSQL_PORT', 3306)),
            'user': self._get_config('MYSQL_USER', 'root'),
            'password': self._get_config('MYSQL_PASSWORD', ''),
            'database': self._get_config('MYSQL_DB', 'narloom'),
            'charset': self._get_config('MYSQL_CHARSET', 'utf8mb4')
        }

    # ---------------- 连接保证 ----------------
    def _ensure_connection(self):
        """确保连接有效，若断开则重连"""
        if not self._connection:
            self._initialize()
        try:
            self._connection.ping(reconnect=True)
        except Exception:
            self._initialize()
        return self._connection

    # ---------------- asset 资产操作 ----------------
    def insert_asset(self, user_id: str, asset_type: str, work_id: str = None) -> Dict:
        """
        插入资产 (asset) 记录到 MySQL 数据库
        """
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_ASSETS', 'assets'))
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

    def update_asset(self, asset_id: str, update_data: Dict) -> Optional[Dict]:
        """
        更新资产 (asset) 记录
        """
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_ASSETS', 'assets'))
        now = datetime.now()

        set_clauses = []
        params = []
        if 'work_id' in update_data:
            set_clauses.append("work_id = %s")
            params.append(update_data['work_id'])
        if 'asset_type' in update_data:
            set_clauses.append("asset_type = %s")
            params.append(update_data['asset_type'])

        if not set_clauses:
            set_clauses.append("updated_at = %s")
            params.append(now)
        else:
            set_clauses.append("updated_at = %s")
            params.append(now)

        params.append(asset_id)

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT asset_id FROM {table} WHERE asset_id = %s", (asset_id,))
            if not cursor.fetchone():
                return None
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE asset_id = %s"
            cursor.execute(sql, params)
            conn.commit()

            cursor.execute(f"SELECT * FROM {table} WHERE asset_id = %s", (asset_id,))
            return cursor.fetchone()

    def delete_asset(self, asset_id: str) -> bool:
        """删除资产记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_ASSETS', 'assets'))

        with conn.cursor() as cursor:
            sql = f"DELETE FROM {table} WHERE asset_id = %s"
            cursor.execute(sql, (asset_id,))
            conn.commit()
            return cursor.rowcount > 0

    def fetch_asset_by_id(self, asset_id: str) -> Optional[Dict]:
        """根据 asset_id 获取资产记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_ASSETS', 'assets'))

        with conn.cursor() as cursor:
            sql = f"SELECT * FROM {table} WHERE asset_id = %s"
            cursor.execute(sql, (asset_id,))
            return cursor.fetchone()

    def fetch_assets(self, user_id: str, asset_type: Optional[str] = None, work_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """根据条件获取资产列表"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_ASSETS', 'assets'))
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

    # ---------------- work 作品操作 ----------------
    def insert_work(self, author_id: str, title: str, genre: str = '', tags=None,
                    status: str = 'draft', chapter_count: int = 0, word_count: int = 0,
                    description: str = '') -> Dict:
        """插入作品记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_WORKS', 'works'))
        work_id = str(uuid.uuid4())
        now = datetime.now()
        if tags is not None and not isinstance(tags, str):
            tags = json.dumps(tags, ensure_ascii=False)
        with conn.cursor() as cursor:
            sql = f"""
                INSERT INTO {table} (work_id, author_id, title, genre, tags, status, word_count, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (work_id, author_id, title, genre, tags, status,
                                 word_count, description, now, now))
            conn.commit()
        return {
            'work_id': work_id,
            'author_id': author_id,
            'title': title,
            'genre': genre,
            'tags': tags,
            'status': status,
            'chapter_count': chapter_count,
            'word_count': word_count,
            'description': description,
            'created_at': now.strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': now.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def update_work(self, work_id: str, update_data: Dict) -> Optional[Dict]:
        """更新作品记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_WORKS', 'works'))
        now = datetime.now()
        allowed_fields = ['title', 'genre', 'tags', 'status', 'word_count', 'description']
        set_clauses = []
        params = []
        for field in allowed_fields:
            if field in update_data:
                value = update_data[field]
                # tags 字段如果是列表，转换为 JSON 字符串
                if field == 'tags' and value is not None and not isinstance(value, str):
                    value = json.dumps(value, ensure_ascii=False)
                set_clauses.append(f"{field} = %s")
                params.append(value)

        set_clauses.append("updated_at = %s")
        params.append(now)
        params.append(work_id)
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT work_id FROM {table} WHERE work_id = %s", (work_id,))
            if not cursor.fetchone():
                return None
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE work_id = %s"
            cursor.execute(sql, params)
            conn.commit()

            cursor.execute(f"SELECT * FROM {table} WHERE work_id = %s", (work_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
                # tags 字段从 JSON 字符串转回 Python 列表
                if row.get('tags'):
                    try:
                        row['tags'] = json.loads(row['tags'])
                    except (json.JSONDecodeError, TypeError):
                        pass
            return row

    def fetch_work_by_id(self, work_id: str) -> Optional[Dict]:
        """根据 work_id 获取作品记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_WORKS', 'works'))

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE work_id = %s", (work_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
                # tags 字段从 JSON 字符串转回 Python 列表
                if row.get('tags'):
                    try:
                        row['tags'] = json.loads(row['tags'])
                    except (json.JSONDecodeError, TypeError):
                        pass
            return row

    def fetch_works_by_author_id(self, author_id: str, status: Optional[str] = None,
                                 limit: int = 100, offset: int = 0) -> List[Dict]:
        """根据作者 ID 获取作品列表"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_WORKS', 'works'))
        conditions = ["author_id = %s"]
        params = [author_id]
        if status:
            conditions.append("status = %s")
            params.append(status)
        sql = f"SELECT * FROM {table} WHERE {' AND '.join(conditions)} ORDER BY updated_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                    row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
                    # tags 字段从 JSON 字符串转回 Python 列表
                    if row.get('tags'):
                        try:
                            row['tags'] = json.loads(row['tags'])
                        except (json.JSONDecodeError, TypeError):
                            pass
            return rows

    def delete_work(self, work_id: str) -> bool:
        """删除作品记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_WORKS', 'works'))

        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE work_id = %s", (work_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ---------------- chapter 章节操作 ----------------
    def insert_chapter(self, work_id: str, author_id: str, chapter_number: int,
                       chapter_title: str = '', content: str = '', status: str = 'draft',
                       word_count: int = 0, description: str = '') -> Dict:
        """插入章节记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))
        chapter_id = str(uuid.uuid4())
        now = datetime.now()
        with conn.cursor() as cursor:
            sql = f"""
                INSERT INTO {table} (chapter_id, work_id, author_id, chapter_num, chapter_title, content, status, word_count, notes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (chapter_id, work_id, author_id, chapter_number,
                                 chapter_title, content, status,
                                 word_count, description,
                                 now, now))
            conn.commit()
        return {
            "chapter_id": chapter_id,
            "work_id": work_id,
            "author_id": author_id,
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "content": content,
            "status": status,
            "word_count": word_count,
            "description": description,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
        }

    def update_chapter(self, chapter_id: str, update_data: Dict) -> Optional[Dict]:
        """更新章节记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))
        now = datetime.now()
        field_mapping = {
            'chapter_number': 'chapter_num',
            'chapter_title': 'chapter_title',
            'content': 'content',
            'status': 'status',
            'word_count': 'word_count',
            'description': 'notes'
        }
        set_clauses = []
        params = []

        for api_field, db_column in field_mapping.items():
            if api_field in update_data:
                set_clauses.append(f"{db_column} = %s")
                params.append(update_data[api_field])

        set_clauses.append("updated_at = %s")
        params.append(now)
        params.append(chapter_id)

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT chapter_id FROM {table} WHERE chapter_id = %s", (chapter_id,))
            if not cursor.fetchone():
                return None
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE chapter_id = %s"
            cursor.execute(sql, params)
            conn.commit()
            cursor.execute(f"SELECT * FROM {table} WHERE chapter_id = %s", (chapter_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_chapter_by_id(self, chapter_id: str) -> Optional[Dict]:
        """根据章节 ID 获取章节记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE chapter_id = %s", (chapter_id,))
            row = cursor.fetchone()
            if row:
                if 'chapter_num' in row:
                    row['chapter_number'] = row.pop('chapter_num')
                if 'notes' in row:
                    row['description'] = row.pop('notes')
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_chapters_by_work_id(self, work_id: str, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """根据作品 ID 获取章节列表"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))
        conditions = ["work_id = %s"]
        params = [work_id]
        if status:
            conditions.append("status = %s")
            params.append(status)
        sql = f"SELECT * FROM {table} WHERE {' AND '.join(conditions)} ORDER BY chapter_num ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    if 'chapter_num' in row:
                        row['chapter_number'] = row.pop('chapter_num')
                    if 'notes' in row:
                        row['description'] = row.pop('notes')
                    row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                    row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return rows

    def delete_chapter(self, chapter_id: str) -> bool:
        """删除章节记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))

        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE chapter_id = %s", (chapter_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ---------------- user 用户操作 ----------------
    def insert_user(self, user_id: str, name: str = '', bio: str = '',
                    email: str = None, password_hash: str = None) -> Dict:
        """插入用户记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_USERS', 'users'))
        now = datetime.now()

        with conn.cursor() as cursor:
            sql = f"""
                INSERT INTO {table} (user_id, email, password_hash, name, bio, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, email, password_hash, name, bio, now, now))
            conn.commit()

        return {
            'user_id': user_id,
            'email': email,
            'name': name,
            'bio': bio,
            'created_at': now.strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': now.strftime("%Y-%m-%d %H:%M:%S")
        }

    def update_user(self, user_id: str, update_data: Dict) -> Optional[Dict]:
        """更新用户记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_USERS', 'users'))
        now = datetime.now()

        set_clauses = []
        params = []
        if 'name' in update_data:
            set_clauses.append("name = %s")
            params.append(update_data['name'])
        if 'bio' in update_data:
            set_clauses.append("bio = %s")
            params.append(update_data['bio'])
        if 'email' in update_data:
            set_clauses.append("email = %s")
            params.append(update_data['email'])
        if 'password_hash' in update_data:
            set_clauses.append("password_hash = %s")
            params.append(update_data['password_hash'])

        if not set_clauses:
            set_clauses.append("updated_at = %s")
            params.append(now)
        else:
            set_clauses.append("updated_at = %s")
            params.append(now)

        params.append(user_id)

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT user_id FROM {table} WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                return None
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE user_id = %s"
            cursor.execute(sql, params)
            conn.commit()

            cursor.execute(f"SELECT * FROM {table} WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_user_by_id(self, user_id: str) -> Optional[Dict]:
        """根据 user_id 获取用户记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_USERS', 'users'))

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_user_by_email(self, email: str) -> Optional[Dict]:
        """根据 email 获取用户记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_USERS', 'users'))

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE email = %s", (email,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def register_user(self, email: str, password: str, name: str = '', bio: str = '') -> Optional[Dict]:
        """注册新用户"""
        existing_user = self.fetch_user_by_email(email)
        if existing_user:
            return None

        # 使用 bcrypt 加密密码
        import bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user_id = str(uuid.uuid4())

        try:
            return self.insert_user(
                user_id=user_id,
                email=email,
                password_hash=password_hash,
                name=name,
                bio=bio
            )
        except Exception as e:
            self._log(f"Error registering user {email}: {e}", level='error')
            return None

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """验证用户邮箱和密码"""
        user = self.fetch_user_by_email(email)
        if not user or not user.get('password_hash'):
            return None

        password_hash = user['password_hash']

        # 使用 bcrypt 验证密码
        import bcrypt
        try:
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return user
        except Exception:
            return None

        return None

    def delete_user(self, user_id: str) -> bool:
        """删除用户记录"""
        conn = self._ensure_connection()
        table = self._validate_table_name(self._get_config('MYSQL_TABLE_USERS', 'users'))

        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==================== OAuth 相关方法 ====================

    def fetch_user_by_oauth(self, provider: str, open_id: str) -> Optional[Dict]:
        """
        通过 OAuth provider 和 open_id 获取用户

        Args:
            provider: OAuth 提供商（wechat, qq）
            open_id: 用户在提供商的唯一 ID

        Returns:
            Dict: 用户记录，包含 user_id, email, name, avatar_url 等
        """
        conn = self._ensure_connection()

        try:
            with conn.cursor() as cursor:
                # 从 user_oauth_accounts 表查找
                cursor.execute("""
                    SELECT u.*, o.provider, o.open_id, o.union_id, o.provider_data
                    FROM user_oauth_accounts o
                    JOIN users u ON o.user_id = u.user_id
                    WHERE o.provider = %s AND o.open_id = %s
                """, (provider, open_id))

                row = cursor.fetchone()
                if row:
                    row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                    row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
                return row

        except Exception as e:
            self._log(f"Error fetching user by OAuth: {e}", level='error')
            return None

    def fetch_user_by_oauth_union_id(self, provider: str, union_id: str) -> Optional[Dict]:
        """
        通过 union_id 获取用户（微信生态跨应用识别）

        Args:
            provider: OAuth 提供商
            union_id: 统一 ID

        Returns:
            Dict: 用户记录
        """
        conn = self._ensure_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT u.*, o.provider, o.open_id, o.union_id
                    FROM user_oauth_accounts o
                    JOIN users u ON o.user_id = u.user_id
                    WHERE o.provider = %s AND o.union_id = %s
                """, (provider, union_id))

                row = cursor.fetchone()
                if row:
                    row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                    row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
                return row

        except Exception as e:
            self._log(f"Error fetching user by union_id: {e}", level='error')
            return None

    def create_oauth_user(self, provider: str, open_id: str,
                          union_id: str = None, provider_data: dict = None,
                          name: str = '', avatar_url: str = None,
                          email: str = None) -> Optional[Dict]:
        """
        创建 OAuth 用户并绑定 OAuth 账号

        Args:
            provider: OAuth 提供商
            open_id: 用户 openid
            union_id: 统一 ID（可选）
            provider_data: 原始用户数据（包含昵称、头像等）
            name: 用户昵称
            avatar_url: 头像 URL
            email: 邮箱（可选）

        Returns:
            Dict: 创建的用户记录
        """
        conn = self._ensure_connection()
        user_id = str(uuid.uuid4())
        now = datetime.now()

        try:
            with conn.cursor() as cursor:
                # 1. 创建用户记录
                users_table = self._validate_table_name(self._get_config('MYSQL_TABLE_USERS', 'users'))
                cursor.execute("""
                    INSERT INTO users (user_id, email, name, avatar_url, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, email, name, avatar_url, now, now))

                # 2. 创建 OAuth 账号绑定记录
                if provider_data:
                    provider_data_json = json.dumps(provider_data, ensure_ascii=False)
                else:
                    provider_data_json = None

                cursor.execute("""
                    INSERT INTO user_oauth_accounts
                    (user_id, provider, open_id, union_id, provider_data, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, provider, open_id, union_id, provider_data_json, now, now))

                conn.commit()

                self._log(f"Created OAuth user: {user_id} for {provider}")

                # 返回用户信息
                return {
                    'user_id': user_id,
                    'email': email,
                    'name': name,
                    'avatar_url': avatar_url,
                    'created_at': now.strftime("%Y-%m-%d %H:%M:%S"),
                    'updated_at': now.strftime("%Y-%m-%d %H:%M:%S")
                }

        except Exception as e:
            conn.rollback()
            self._log(f"Error creating OAuth user: {e}", level='error')
            return None

    def bind_oauth_account(self, user_id: str, provider: str,
                           open_id: str, union_id: str = None,
                           access_token: str = None,
                           access_token_expires_at: datetime = None,
                           refresh_token: str = None,
                           provider_data: dict = None) -> bool:
        """
        为现有用户绑定 OAuth 账号

        Args:
            user_id: 用户 ID
            provider: OAuth 提供商
            open_id: 用户 openid
            union_id: 统一 ID
            access_token: OAuth 访问令牌
            access_token_expires_at: 令牌过期时间
            refresh_token: OAuth 刷新令牌
            provider_data: 原始用户数据

        Returns:
            bool: 是否绑定成功
        """
        conn = self._ensure_connection()
        now = datetime.now()

        try:
            with conn.cursor() as cursor:
                # 检查是否已绑定
                cursor.execute("""
                    SELECT id FROM user_oauth_accounts
                    WHERE provider = %s AND open_id = %s
                """, (provider, open_id))

                if cursor.fetchone():
                    self._log(f"OAuth account already bound: {provider}:{open_id}")
                    return False

                # 绑定 OAuth 账号
                if provider_data:
                    provider_data_json = json.dumps(provider_data, ensure_ascii=False)
                else:
                    provider_data_json = None

                cursor.execute("""
                    INSERT INTO user_oauth_accounts
                    (user_id, provider, open_id, union_id, access_token, access_token_expires_at,
                     refresh_token, provider_data, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, provider, open_id, union_id, access_token,
                      access_token_expires_at, refresh_token, provider_data_json, now, now))

                conn.commit()
                self._log(f"Bound OAuth account: {provider}:{open_id} to user {user_id}")
                return True

        except Exception as e:
            conn.rollback()
            self._log(f"Error binding OAuth account: {e}", level='error')
            return False

    def unbind_oauth_account(self, user_id: str, provider: str) -> bool:
        """
        解绑 OAuth 账号

        Args:
            user_id: 用户 ID
            provider: OAuth 提供商

        Returns:
            bool: 是否解绑成功
        """
        conn = self._ensure_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM user_oauth_accounts
                    WHERE user_id = %s AND provider = %s
                """, (user_id, provider))

                conn.commit()
                deleted_count = cursor.rowcount

                if deleted_count > 0:
                    self._log(f"Unbound OAuth account: {provider} from user {user_id}")

                return deleted_count > 0

        except Exception as e:
            conn.rollback()
            self._log(f"Error unbinding OAuth account: {e}", level='error')
            return False

    def update_user_last_login(self, user_id: str, provider: str) -> bool:
        """
        更新用户最后登录时间和方式

        Args:
            user_id: 用户 ID
            provider: 登录提供商

        Returns:
            bool: 是否更新成功
        """
        conn = self._ensure_connection()
        users_table = self._validate_table_name(self._get_config('MYSQL_TABLE_USERS', 'users'))

        try:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE {users_table}
                    SET last_login_at = %s, last_login_provider = %s, updated_at = %s
                    WHERE user_id = %s
                """, (datetime.now(), provider, datetime.now(), user_id))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            self._log(f"Error updating last login: {e}", level='error')
            return False

    def fetch_user_oauth_accounts(self, user_id: str) -> List[Dict]:
        """
        获取用户绑定的所有 OAuth 账号

        Args:
            user_id: 用户 ID

        Returns:
            List[Dict]: OAuth 账号列表
        """
        conn = self._ensure_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT provider, open_id, union_id, created_at, updated_at
                    FROM user_oauth_accounts
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))

                rows = cursor.fetchall()
                result = []
                for row in rows:
                    result.append({
                        'provider': row['provider'],
                        'open_id': row['open_id'],
                        'union_id': row.get('union_id'),
                        'created_at': row['created_at'].strftime("%Y-%m-%d %H:%M:%S"),
                        'updated_at': row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
                    })
                return result

        except Exception as e:
            self._log(f"Error fetching user OAuth accounts: {e}", level='error')
            return []

    def update_oauth_tokens(self, user_id: str, provider: str,
                            access_token: str = None,
                            access_token_expires_at: datetime = None,
                            refresh_token: str = None) -> bool:
        """
        更新 OAuth 令牌

        Args:
            user_id: 用户 ID
            provider: OAuth 提供商
            access_token: 新的访问令牌
            access_token_expires_at: 令牌过期时间
            refresh_token: 新的刷新令牌

        Returns:
            bool: 是否更新成功
        """
        conn = self._ensure_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_oauth_accounts
                    SET access_token = %s, access_token_expires_at = %s,
                        refresh_token = %s, updated_at = %s
                    WHERE user_id = %s AND provider = %s
                """, (access_token, access_token_expires_at, refresh_token,
                      datetime.now(), user_id, provider))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            self._log(f"Error updating OAuth tokens: {e}", level='error')
            return False


mysql_service = MySQLService()
