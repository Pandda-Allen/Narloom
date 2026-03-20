"""
OAuth2.0 基础服务类
提供通用的 OAuth2.0 授权流程实现
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging

from ..base_service import BaseService
from ..mysql_service import MySQLService

logger = logging.getLogger(__name__)


class BaseOAuthService(BaseService, ABC):
    """
    OAuth2.0 基础服务类

    子类需要实现以下方法：
    - get_authorization_url()
    - exchange_code_for_token()
    - get_user_info()
    """

    PROVIDER_NAME = 'base'

    def _initialize(self):
        """初始化配置"""
        self._initialized = True

    def _get_config(self, key: str, default=None):
        """从 Config 获取配置"""
        from config import Config
        return getattr(Config, key, default)

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """
        获取授权 URL

        Args:
            state: CSRF 防护参数

        Returns:
            str: 授权页面 URL
        """
        pass

    @abstractmethod
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        用授权码换取访问令牌

        Args:
            code: 授权码

        Returns:
            Dict: 包含 access_token, expires_in, refresh_token, openid 等
        """
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        获取用户信息

        Args:
            access_token: 访问令牌

        Returns:
            Dict: 用户信息
        """
        pass

    def generate_state(self) -> str:
        """
        生成随机 state 参数（用于 CSRF 防护）

        Returns:
            str: 随机 state 字符串
        """
        return secrets.token_urlsafe(32)

    def save_state(self, state: str, provider: str, action: str = 'login',
                   user_id: str = None, expires_minutes: int = 10) -> bool:
        """
        保存 state 到数据库

        Args:
            state: state 参数
            provider: OAuth 提供商
            action: 操作类型（login/bind）
            user_id: 用户 ID（绑定场景需要）
            expires_minutes: 过期时间（分钟）

        Returns:
            bool: 是否保存成功
        """
        try:
            mysql = MySQLService()
            conn = mysql._ensure_connection()

            expires_at = datetime.now() + timedelta(minutes=expires_minutes)

            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO oauth_states (state, user_id, provider, action, created_at, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (state, user_id, provider, action, datetime.now(), expires_at))

                conn.commit()
                logger.info(f"Saved OAuth state: {state[:8]}... for {provider}")
                return True

        except Exception as e:
            logger.error(f"Error saving OAuth state: {e}")
            return False

    def validate_state(self, state: str, provider: str, action: str = None) -> bool:
        """
        验证 state 参数

        Args:
            state: state 参数
            provider: OAuth 提供商
            action: 期望的操作类型

        Returns:
            bool: 是否有效
        """
        try:
            mysql = MySQLService()
            conn = mysql._ensure_connection()

            with conn.cursor() as cursor:
                # 查找未消耗的 state
                cursor.execute("""
                    SELECT id, user_id, action FROM oauth_states
                    WHERE state = %s AND provider = %s
                    AND expires_at > NOW()
                    AND consumed_at IS NULL
                """, (state, provider))

                result = cursor.fetchone()

                if not result:
                    logger.warning(f"Invalid or expired OAuth state: {state[:8]}...")
                    return False

                # 如果指定了 action，验证是否匹配
                if action and result[2] != action:
                    logger.warning(f"OAuth state action mismatch: expected {action}, got {result[2]}")
                    return False

                # 标记为已消耗
                cursor.execute("""
                    UPDATE oauth_states
                    SET consumed_at = %s, consumed_by_action = %s
                    WHERE state = %s
                """, (datetime.now(), action or result[2], state))

                conn.commit()
                logger.info(f"Validated OAuth state: {state[:8]}...")

                return True

        except Exception as e:
            logger.error(f"Error validating OAuth state: {e}")
            return False

    def get_state_user_id(self, state: str) -> Optional[str]:
        """
        获取 state 关联的用户 ID

        Args:
            state: state 参数

        Returns:
            str: 用户 ID 或 None
        """
        try:
            mysql = MySQLService()
            conn = mysql._ensure_connection()

            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT user_id FROM oauth_states
                    WHERE state = %s AND consumed_at IS NULL
                """, (state,))

                result = cursor.fetchone()
                return result[0] if result else None

        except Exception as e:
            logger.error(f"Error getting state user_id: {e}")
            return None

    def parse_error_response(self, error_data: Dict) -> str:
        """
        解析错误响应

        Args:
            error_data: 错误数据

        Returns:
            str: 错误信息
        """
        if 'error' in error_data:
            error = error_data['error']
            error_description = error_data.get('error_description', str(error))
            return f"OAuth error: {error_description}"
        return "Unknown OAuth error"

    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return self.PROVIDER_NAME
