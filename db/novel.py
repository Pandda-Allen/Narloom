"""
Novel 数据访问层
负责 novels 表的 CRUD 操作（原 chapters 表）
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from .base_service import mysql_base_service


class NovelService:
    """Novel 数据访问类（原 ChapterService）"""

    def insert_novel(self, work_id: str, author_id: str, novel_number: int,
                     novel_title: str = '', content: str = '', status: str = 'draft',
                     word_count: int = 0, description: str = '', notes: str = '') -> Dict:
        """插入小说章节记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_NOVELS', 'novels'))
        novel_id = str(uuid.uuid4())
        now = datetime.now()

        with conn.cursor() as cursor:
            sql = f"""
                INSERT INTO {table} (novel_id, work_id, author_id, novel_number, novel_title, content, status, word_count, description, notes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (novel_id, work_id, author_id, novel_number,
                                 novel_title, content, status,
                                 word_count, description, notes,
                                 now, now))
            conn.commit()

        return {
            "novel_id": novel_id,
            "work_id": work_id,
            "author_id": author_id,
            "novel_number": novel_number,
            "novel_title": novel_title,
            "content": content,
            "status": status,
            "word_count": word_count,
            "description": description,
            "notes": notes,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
        }

    def update_novel(self, novel_id: str, update_data: Dict) -> Optional[Dict]:
        """更新小说章节记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_NOVELS', 'novels'))
        now = datetime.now()

        field_mapping = {
            'novel_number': 'novel_number',
            'novel_title': 'novel_title',
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
        params.append(novel_id)

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT novel_id FROM {table} WHERE novel_id = %s", (novel_id,))
            if not cursor.fetchone():
                return None
            sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE novel_id = %s"
            cursor.execute(sql, params)
            conn.commit()

            cursor.execute(f"SELECT * FROM {table} WHERE novel_id = %s", (novel_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_novel_by_id(self, novel_id: str) -> Optional[Dict]:
        """根据小说章节 ID 获取记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_NOVELS', 'novels'))

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE novel_id = %s", (novel_id,))
            row = cursor.fetchone()
            if row:
                if 'novel_number' in row:
                    row['novel_number'] = row['novel_number']
                if 'notes' in row:
                    row['description'] = row.pop('notes')
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_novels_by_work_id(self, work_id: str, status: Optional[str] = None,
                                 limit: int = 100, offset: int = 0) -> List[Dict]:
        """根据作品 ID 获取小说章节列表"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_NOVELS', 'novels'))
        conditions = ["work_id = %s"]
        params = [work_id]

        if status:
            conditions.append("status = %s")
            params.append(status)

        sql = f"SELECT * FROM {table} WHERE {' AND '.join(conditions)} ORDER BY novel_number ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    if 'notes' in row:
                        row['description'] = row.pop('notes')
                    row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                    row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return rows

    def delete_novel(self, novel_id: str) -> bool:
        """删除小说章节记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_NOVELS', 'novels'))

        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE novel_id = %s", (novel_id,))
            conn.commit()
            return cursor.rowcount > 0


novel_service = NovelService()
