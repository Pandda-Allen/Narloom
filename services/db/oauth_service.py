"""
OAuth 数据访问层
负责 user_oauth_accounts 表的 CRUD 操作
"""
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, List
from .base_service import mysql_base_service


class OAuthService:
    """OAuth 数据访问类"""

    def fetch_user_by_oauth(self, provider: str, open_id: str) -> Optional[Dict]:
        """通过 OAuth provider 和 open_id 获取用户"""
        conn = mysql_base_service._ensure_connection()

        try:
            with conn.cursor() as cursor:
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
            mysql_base_service._log(f"Error fetching user by OAuth: {e}", level='error')
            return None

    def fetch_user_by_oauth_union_id(self, provider: str, union_id: str) -> Optional[Dict]:
        """通过 union_id 获取用户（微信生态跨应用识别）"""
        conn = mysql_base_service._ensure_connection()

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
            mysql_base_service._log(f"Error fetching user by union_id: {e}", level='error')
            return None

    def create_oauth_user(self, provider: str, open_id: str,
                          union_id: str = None, provider_data: dict = None,
                          name: str = '', avatar_url: str = None,
                          email: str = None) -> Optional[Dict]:
        """创建 OAuth 用户并绑定 OAuth 账号"""
        conn = mysql_base_service._ensure_connection()
        user_id = str(uuid.uuid4())
        now = datetime.now()

        try:
            with conn.cursor() as cursor:
                # 1. 创建用户记录
                users_table = mysql_base_service._validate_table_name(
                    mysql_base_service._get_config('MYSQL_TABLE_USERS', 'users'))
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
                mysql_base_service._log(f"Created OAuth user: {user_id} for {provider}")

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
            mysql_base_service._log(f"Error creating OAuth user: {e}", level='error')
            return None

    def bind_oauth_account(self, user_id: str, provider: str,
                           open_id: str, union_id: str = None,
                           access_token: str = None,
                           access_token_expires_at: datetime = None,
                           refresh_token: str = None,
                           provider_data: dict = None) -> bool:
        """为现有用户绑定 OAuth 账号"""
        conn = mysql_base_service._ensure_connection()
        now = datetime.now()

        try:
            with conn.cursor() as cursor:
                # 检查是否已绑定
                cursor.execute("""
                    SELECT id FROM user_oauth_accounts
                    WHERE provider = %s AND open_id = %s
                """, (provider, open_id))

                if cursor.fetchone():
                    mysql_base_service._log(f"OAuth account already bound: {provider}:{open_id}")
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
                mysql_base_service._log(f"Bound OAuth account: {provider}:{open_id} to user {user_id}")
                return True

        except Exception as e:
            conn.rollback()
            mysql_base_service._log(f"Error binding OAuth account: {e}", level='error')
            return False

    def unbind_oauth_account(self, user_id: str, provider: str) -> bool:
        """解绑 OAuth 账号"""
        conn = mysql_base_service._ensure_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM user_oauth_accounts
                    WHERE user_id = %s AND provider = %s
                """, (user_id, provider))

                conn.commit()
                deleted_count = cursor.rowcount

                if deleted_count > 0:
                    mysql_base_service._log(f"Unbound OAuth account: {provider} from user {user_id}")

                return deleted_count > 0

        except Exception as e:
            conn.rollback()
            mysql_base_service._log(f"Error unbinding OAuth account: {e}", level='error')
            return False

    def fetch_user_oauth_accounts(self, user_id: str) -> List[Dict]:
        """获取用户绑定的所有 OAuth 账号"""
        conn = mysql_base_service._ensure_connection()

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
            mysql_base_service._log(f"Error fetching user OAuth accounts: {e}", level='error')
            return []

    def update_oauth_tokens(self, user_id: str, provider: str,
                            access_token: str = None,
                            access_token_expires_at: datetime = None,
                            refresh_token: str = None) -> bool:
        """更新 OAuth 令牌"""
        conn = mysql_base_service._ensure_connection()

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
            mysql_base_service._log(f"Error updating OAuth tokens: {e}", level='error')
            return False


oauth_service = OAuthService()
