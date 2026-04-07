"""
资产数据访问层
负责 assets 表的 CRUD 操作
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from .base_service import mysql_base_service


class AssetService:
    """资产数据访问类"""

    def insert_asset(self, user_id: str, asset_type: str, work_id: str = None) -> Dict:
        """插入资产记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_ASSETS', 'assets'))
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
        """更新资产记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_ASSETS', 'assets'))
        now = datetime.now()

        set_clauses = []
        params = []
        if 'work_id' in update_data:
            set_clauses.append("work_id = %s")
            params.append(update_data['work_id'])
        if 'asset_type' in update_data:
            set_clauses.append("asset_type = %s")
            params.append(update_data['asset_type'])

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
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_ASSETS', 'assets'))

        with conn.cursor() as cursor:
            sql = f"DELETE FROM {table} WHERE asset_id = %s"
            cursor.execute(sql, (asset_id,))
            conn.commit()
            return cursor.rowcount > 0

    def fetch_asset_by_id(self, asset_id: str) -> Optional[Dict]:
        """根据 asset_id 获取资产记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_ASSETS', 'assets'))

        with conn.cursor() as cursor:
            sql = f"SELECT * FROM {table} WHERE asset_id = %s"
            cursor.execute(sql, (asset_id,))
            return cursor.fetchone()

    def fetch_assets(self, user_id: str, asset_type: Optional[str] = None,
                     work_id: Optional[str] = None, limit: int = 100,
                     offset: int = 0) -> List[Dict]:
        """根据条件获取资产列表"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_ASSETS', 'assets'))
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


asset_service = AssetService()
