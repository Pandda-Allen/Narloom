import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import pymysql
import pymysql.cursors
from .base_service import BaseService

class MySQLService(BaseService):
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
            # 确保users表存在
            self._create_users_table_if_not_exists()
            self._initialized = True
            self._log("MySQL service initialized successfully")
        except Exception as e:
            self._log(f"Error initializing MySQL service: {e}", level='error')
            raise

    def _create_users_table_if_not_exists(self):
        """创建users表（如果不存在）"""
        conn = self._connection
        table = self._get_config('MYSQL_TABLE_USERS', 'users')
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        user_id VARCHAR(100) PRIMARY KEY,
                        name VARCHAR(255) DEFAULT '',
                        bio TEXT,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                conn.commit()
                self._log(f"Table '{table}' ensured")
        except Exception as e:
            self._log(f"Error creating table {table}: {e}", level='error')
            # 不抛出异常，允许连接继续
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
    
    # ---------------- asset 资产操作 ----------------
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
    
    def update_asset(self, asset_id: str, update_data: Dict) -> Optional[Dict]:
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
        
    # ---------------- work 作品操作 ----------------
    def insert_work(self, author_id: str, title: str, genre: str = '', tags=None,
                    status: str = 'draft', chapter_count: int = 0, word_count: int = 0,
                    description: str = '') -> Dict:
        """
        插入作品(work)记录到MySQL数据库
        :return: 插入的行数据(包含 work_id, created_at, updated_at)
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_WORKS', 'works')
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
        """
        更新作品(work)记录到MySQL数据库
        :return: 更新的行数据(包含 work_id, updated_at)
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_WORKS', 'works')
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
            # 先检查作品是否存在
            cursor.execute(f"SELECT work_id FROM {table} WHERE work_id = %s", (work_id,))
            if not cursor.fetchone():
                return None
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE work_id = %s"
            cursor.execute(sql, params)
            conn.commit()

            # 返回更新后的完整行数据
            cursor.execute(f"SELECT * FROM {table} WHERE work_id = %s", (work_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row
    
    def fetch_work_by_id(self, work_id: str) -> Optional[Dict]:
        """
        根据 work_id 从MySQL数据库获取作品(work)记录
        :return: 作品记录字典，若不存在返回 None
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_WORKS', 'works')

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE work_id = %s", (work_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_works_by_author_id(self, author_id: str, status: Optional[str] = None,
                                 limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        根据作者ID从MySQL数据库获取作者的章节列表
        :return: 章节列表字典列表
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_WORKS', 'works')
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
        """
        根据 work_id 从MySQL数据库删除作品(work)记录
        :return: 删除成功返回 True，否则返回 False
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_WORKS', 'works')

        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE work_id = %s", (work_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ---------------- chapter 章节操作 ----------------
    def insert_chapter(self, work_id: str, author_id: str, chapter_number: int,
                       chapter_title: str = '', content: str = '', status: str = 'draft',
                       word_count: int = 0, description: str = '') -> Dict:
        """
        向MySQL数据库插入章节记录
        :return: 章节记录字典
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters')
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
        """
        更新MySQL数据库中的章节记录
        :param chapter_id: 章节ID
        :param update_data: 更新的数据字典
        :return: 更新后的章节记录字典，若不存在返回 None
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters')
        now = datetime.now()
        # 字段映射：API字段名 -> 数据库列名
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
        """
        根据章节ID从MySQL数据库获取章节记录
        :return: 章节记录字典，若不存在返回 None
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters')

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE chapter_id = %s", (chapter_id,))
            row = cursor.fetchone()
            if row:
                # 映射数据库列名到API字段名
                if 'chapter_num' in row:
                    row['chapter_number'] = row.pop('chapter_num')
                if 'notes' in row:
                    row['description'] = row.pop('notes')
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_chapters_by_work_id(self, work_id: str, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        根据作品ID从MySQL数据库获取章节列表
        :return: 章节记录字典列表
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters')
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
                    # 映射数据库列名到API字段名
                    if 'chapter_num' in row:
                        row['chapter_number'] = row.pop('chapter_num')
                    if 'notes' in row:
                        row['description'] = row.pop('notes')
                    row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                    row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return rows
        
    def delete_chapter(self, chapter_id: str) -> bool:
        """
        从MySQL数据库删除章节记录
        :param chapter_id: 章节ID
        :return: 是否成功删除
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_CHAPTERS', 'chapters')

        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE chapter_id = %s", (chapter_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ---------------- user 用户操作 ----------------
    def insert_user(self, user_id: str, name: str = '', bio: str = '') -> Dict:
        """
        插入用户记录到MySQL数据库
        :return: 插入的行数据(包含 user_id, name, bio, created_at, updated_at)
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_USERS', 'users')
        now = datetime.now()

        with conn.cursor() as cursor:
            sql = f"""
                INSERT INTO {table} (user_id, name, bio, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (user_id, name, bio, now, now))
            conn.commit()

        return {
            'user_id': user_id,
            'name': name,
            'bio': bio,
            'created_at': now.strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': now.strftime("%Y-%m-%d %H:%M:%S")
        }

    def update_user(self, user_id: str, update_data: Dict) -> Optional[Dict]:
        """
        更新用户记录到MySQL数据库(仅允许更新name, bio)
        :param update_data: 可包含'name', 'bio'的字典
        :return: 更新后的完整行数据，若用户不存在返回 None
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_USERS', 'users')
        now = datetime.now()

        # 构建 SET 语句
        set_clauses = []
        params = []
        if 'name' in update_data:
            set_clauses.append("name = %s")
            params.append(update_data['name'])
        if 'bio' in update_data:
            set_clauses.append("bio = %s")
            params.append(update_data['bio'])

        if not set_clauses:
            # 没有要更新的字段，但仍需更新时间戳
            set_clauses.append("updated_at = %s")
            params.append(now)
        else:
            set_clauses.append("updated_at = %s")
            params.append(now)

        params.append(user_id)

        with conn.cursor() as cursor:
            # 先检查用户是否存在
            cursor.execute(f"SELECT user_id FROM {table} WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                return None
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE user_id = %s"
            cursor.execute(sql, params)
            conn.commit()

            # 返回更新后的完整行数据
            cursor.execute(f"SELECT * FROM {table} WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        根据 user_id 从MySQL数据库获取用户记录
        :return: 用户记录字典，若不存在返回 None
        """
        conn = self._ensure_connection()
        table = self._get_config('MYSQL_TABLE_USERS', 'users')

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

mysql_service = MySQLService()