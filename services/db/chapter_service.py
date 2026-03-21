"""
章节数据访问层
负责 chapters 表的 CRUD 操作
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from .base_service import mysql_base_service


class ChapterService:
    """章节数据访问类"""

    def insert_chapter(self, work_id: str, author_id: str, chapter_number: int,
                       chapter_title: str = '', content: str = '', status: str = 'draft',
                       word_count: int = 0, description: str = '') -> Dict:
        """插入章节记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))
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
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))
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
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE chapter_id = %s", (chapter_id,))
            row = cursor.fetchone()
            if row:
                # 字段名转换：chapter_num -> chapter_number, notes -> description
                if 'chapter_num' in row:
                    row['chapter_number'] = row.pop('chapter_num')
                if 'notes' in row:
                    row['description'] = row.pop('notes')
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_chapters_by_work_id(self, work_id: str, status: Optional[str] = None,
                                  limit: int = 100, offset: int = 0) -> List[Dict]:
        """根据作品 ID 获取章节列表"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))
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
                    # 字段名转换
                    if 'chapter_num' in row:
                        row['chapter_number'] = row.pop('chapter_num')
                    if 'notes' in row:
                        row['description'] = row.pop('notes')
                    row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                    row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return rows

    def delete_chapter(self, chapter_id: str) -> bool:
        """删除章节记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_CHAPTERS', 'chapters'))

        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE chapter_id = %s", (chapter_id,))
            conn.commit()
            return cursor.rowcount > 0


chapter_service = ChapterService()
