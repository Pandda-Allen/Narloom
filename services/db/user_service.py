"""
用户数据访问层
负责 users 表的 CRUD 操作
"""
import uuid
import bcrypt
from datetime import datetime
from typing import Optional, Dict, List
from .base_service import mysql_base_service


class UserService:
    """用户数据访问类"""

    def insert_user(self, user_id: str, name: str = '', bio: str = '',
                    email: str = None, password_hash: str = None) -> Dict:
        """插入用户记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_USERS', 'users'))
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
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_USERS', 'users'))
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
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_USERS', 'users'))

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table} WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                row['created_at'] = row['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                row['updated_at'] = row['updated_at'].strftime("%Y-%m-%d %H:%M:%S")
            return row

    def fetch_user_by_email(self, email: str) -> Optional[Dict]:
        """根据 email 获取用户记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_USERS', 'users'))

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
            mysql_base_service._log(f"Error registering user {email}: {e}", level='error')
            return None

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """验证用户邮箱和密码"""
        user = self.fetch_user_by_email(email)
        if not user or not user.get('password_hash'):
            return None

        password_hash = user['password_hash']

        # 使用 bcrypt 验证密码
        try:
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return user
        except Exception:
            return None

        return None

    def delete_user(self, user_id: str) -> bool:
        """删除用户记录"""
        conn = mysql_base_service._ensure_connection()
        table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_USERS', 'users'))

        with conn.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_user_last_login(self, user_id: str) -> bool:
        """更新用户最后登录时间"""
        conn = mysql_base_service._ensure_connection()
        users_table = mysql_base_service._validate_table_name(
            mysql_base_service._get_config('MYSQL_TABLE_USERS', 'users'))

        try:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE {users_table}
                    SET last_login_at = %s, updated_at = %s
                    WHERE user_id = %s
                """, (datetime.now(), datetime.now(), user_id))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            mysql_base_service._log(f"Error updating last login: {e}", level='error')
            return False


user_service = UserService()
