"""
作品数据访问层
负责 works 表的 CRUD 操作
"""
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, List
from .base_service import mysql_base_service


class WorkService:
    """作品数据访问类"""

    def insert_work(self, author_id: str, title: str, genre: str = '', tags=None,
                    status: str = 'draft', chapter_count: int = 0, word_count: int = 0,
                    description: str = '') -> Dict:
        """插入作品记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_WORKS', 'works'))
        work_id = str(uuid.uuid4())
        now = datetime.now()

        # tags 字段如果是列表，转换为 JSON 字符串
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
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_WORKS', 'works'))
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
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_WORKS', 'works'))

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
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_WORKS', 'works'))
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
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_WORKS', 'works'))

        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE work_id = %s", (work_id,))
            conn.commit()
            return cursor.rowcount > 0


work_service = WorkService()
