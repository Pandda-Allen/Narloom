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
    'users', 'assets', 'works', 'chapters'
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
                        email VARCHAR(255) UNIQUE,
                        password_hash VARCHAR(255),
                        name VARCHAR(255) DEFAULT '',
                        bio TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        INDEX idx_email (email)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                conn.commit()
                self._log("Table 'users' ensured")
        except Exception as e:
            self._log(f"Error creating table users: {e}", level='error')
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
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
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
                INSERT INTO {table} (work_id, author_id, title, genre, status, word_count, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (work_id, author_id, title, genre, status,
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
        allowed_fields = ['title', 'genre', 'status', 'word_count', 'description']
        set_clauses = []
        params = []
        for field in allowed_fields:
            if field in update_data:
                set_clauses.append(f"{field} = %s")
                params.append(update_data[field])

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

        try:
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password)
        except ImportError:
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()

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

        try:
            from werkzeug.security import check_password_hash
            if check_password_hash(password_hash, password):
                return user
        except ImportError:
            import hashlib
            if password_hash == hashlib.sha256(password.encode()).hexdigest():
                return user

        return None

mysql_service = MySQLService()
