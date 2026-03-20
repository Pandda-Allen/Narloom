"""
Token Blacklist 服务类
管理 JWT 令牌黑名单，用于令牌撤销和登出功能
"""
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from .base_service import BaseService
from .mysql_service import MySQLService

logger = logging.getLogger(__name__)


class TokenBlacklistService(BaseService):
    """
    令牌黑名单服务（基于 MySQL）
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_app(self, app):
        with app.app_context():
            self._initialize()

    def _initialize(self):
        """初始化黑名单表"""
        if self._initialized:
            return

        self._enabled = self._get_config('JWT_BLACKLIST_ENABLED', True)
        self._create_blacklist_table_if_not_exists()
        self._initialized = True

    def _get_config(self, key: str, default=None):
        """从 Config 获取配置"""
        from config import Config
        return getattr(Config, key, default)

    def _create_blacklist_table_if_not_exists(self):
        """创建 token_blacklist 表"""
        mysql = MySQLService()
        conn = mysql._ensure_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_blacklist (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    jti VARCHAR(100) NOT NULL UNIQUE COMMENT 'JWT ID',
                    user_id VARCHAR(100) COMMENT '用户 ID',
                    token_type VARCHAR(20) NOT NULL DEFAULT 'access' COMMENT '令牌类型',
                    blacklisted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL COMMENT '令牌原始过期时间',
                    reason VARCHAR(50) DEFAULT 'logout' COMMENT '加入黑名单原因',
                    INDEX idx_jti (jti),
                    INDEX idx_user_id (user_id),
                    INDEX idx_expires_at (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='JWT 令牌黑名单表'
            """)
            conn.commit()

    def add_to_blacklist(self, jti: str, expires_at: datetime, user_id: str = None,
                         token_type: str = 'access', reason: str = 'logout') -> bool:
        """
        将令牌加入黑名单

        Args:
            jti: JWT ID
            expires_at: 令牌过期时间
            user_id: 用户 ID
            token_type: 令牌类型 (access/refresh)
            reason: 加入黑名单原因

        Returns:
            bool: 是否成功添加
        """
        if not self._enabled:
            return False

        try:
            mysql = MySQLService()
            conn = mysql._ensure_connection()

            with conn.cursor() as cursor:
                # 检查是否已在黑名单中
                cursor.execute("""
                    SELECT id FROM token_blacklist WHERE jti = %s
                """, (jti,))

                if cursor.fetchone():
                    # 已在黑名单中，更新信息
                    cursor.execute("""
                        UPDATE token_blacklist
                        SET blacklisted_at = %s, reason = %s
                        WHERE jti = %s
                    """, (datetime.now(), reason, jti))
                else:
                    # 添加到黑名单
                    cursor.execute("""
                        INSERT INTO token_blacklist (jti, user_id, token_type, blacklisted_at, expires_at, reason)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (jti, user_id, token_type, datetime.now(), expires_at, reason))

                conn.commit()
                logger.info(f"Added JTI {jti} to blacklist")
                return True

        except Exception as e:
            logger.error(f"Error adding to blacklist: {e}")
            return False

    def is_blacklisted(self, jti: str) -> bool:
        """
        检查令牌是否在黑名单中

        Args:
            jti: JWT ID

        Returns:
            bool: 是否在黑名单中
        """
        if not self._enabled:
            return False

        try:
            mysql = MySQLService()
            conn = mysql._ensure_connection()

            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM token_blacklist
                    WHERE jti = %s AND expires_at > NOW()
                """, (jti,))

                result = cursor.fetchone()
                return result is not None

        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
            return False

    def remove_expired_tokens(self) -> int:
        """
        清理过期的黑名单记录

        Returns:
            int: 清理的记录数
        """
        try:
            mysql = MySQLService()
            conn = mysql._ensure_connection()

            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM token_blacklist
                    WHERE expires_at < NOW()
                """)
                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired blacklist entries")

                return deleted_count

        except Exception as e:
            logger.error(f"Error removing expired tokens: {e}")
            return 0

    def blacklist_user_tokens(self, user_id: str, reason: str = 'logout') -> int:
        """
        将用户的所有活跃令牌加入黑名单（用于强制登出）

        Args:
            user_id: 用户 ID
            reason: 加入黑名单原因

        Returns:
            int: 加入黑名单的令牌数量

        Note:
            这个方法主要用于刷新令牌撤销的场景。由于 access token 的 JTI 在每次生成时都不同，
            这个方法主要用于标记该用户的刷新令牌应该被拒绝。实际实现中需要在验证刷新令牌时
            检查用户是否有相关的撤销记录。
        """
        try:
            mysql = MySQLService()
            conn = mysql._ensure_connection()

            with conn.cursor() as cursor:
                # 添加一个特殊的黑名单记录，标记该用户的所有刷新令牌应被撤销
                special_jti = f"user_{user_id}_all_refresh_tokens"
                cursor.execute("""
                    INSERT INTO token_blacklist (jti, user_id, token_type, blacklisted_at, expires_at, reason)
                    VALUES (%s, %s, 'refresh', %s, %s, %s)
                    ON DUPLICATE KEY UPDATE blacklisted_at = %s, reason = %s
                """, (special_jti, user_id, datetime.now(),
                      datetime.now() + timedelta(days=30), reason,
                      datetime.now(), reason))

                conn.commit()
                logger.info(f"Blacklisted all refresh tokens for user {user_id}")
                return 1

        except Exception as e:
            logger.error(f"Error blacklisting user tokens: {e}")
            return 0

    def is_user_tokens_blacklisted(self, user_id: str) -> bool:
        """
        检查用户的所有令牌是否被撤销

        Args:
            user_id: 用户 ID

        Returns:
            bool: 是否被撤销
        """
        try:
            mysql = MySQLService()
            conn = mysql._ensure_connection()

            with conn.cursor() as cursor:
                special_jti = f"user_{user_id}_all_refresh_tokens"
                cursor.execute("""
                    SELECT id FROM token_blacklist
                    WHERE jti = %s AND expires_at > NOW()
                """, (special_jti,))

                return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"Error checking user tokens blacklist: {e}")
            return False

    def get_blacklisted_tokens_count(self, user_id: str = None) -> int:
        """
        获取黑名单中的令牌数量

        Args:
            user_id: 用户 ID（可选）

        Returns:
            int: 黑名单中的令牌数量
        """
        try:
            mysql = MySQLService()
            conn = mysql._ensure_connection()

            with conn.cursor() as cursor:
                if user_id:
                    cursor.execute("""
                        SELECT COUNT(*) AS cnt FROM token_blacklist
                        WHERE user_id = %s AND expires_at > NOW()
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT COUNT(*) AS cnt FROM token_blacklist
                        WHERE expires_at > NOW()
                    """)

                result = cursor.fetchone()
                return int(result['cnt']) if result else 0

        except Exception as e:
            logger.error(f"Error getting blacklisted tokens count: {e}")
            return 0


# 全局实例
token_blacklist_service = TokenBlacklistService()
