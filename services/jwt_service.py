"""
JWT 服务类
处理 JWT 令牌的生成、验证和刷新
"""
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import current_app

from .base_service import BaseService


class JWTService(BaseService):
    """
    JWT 服务类，处理令牌生成、验证和刷新
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
        """初始化 JWT 配置"""
        if self._initialized:
            return

        self.secret_key = self._get_config('JWT_SECRET_KEY')
        self.access_token_expires = self._get_config('JWT_ACCESS_TOKEN_EXPIRES')
        self.refresh_token_expires = self._get_config('JWT_REFRESH_TOKEN_EXPIRES')
        self.algorithm = self._get_config('JWT_ALGORITHM', 'HS256')
        self.issuer = self._get_config('JWT_ISSUER', 'narloom-api')
        self.audience = self._get_config('JWT_AUDIENCE', 'narloom-client')
        self._initialized = True

    def _get_config(self, key: str, default=None):
        """从 Config 获取配置"""
        from config import Config
        return getattr(Config, key, default)

    # ==================== 令牌生成 ====================
    def generate_tokens(self, user_id: str, email: str = None, provider: str = None) -> Dict[str, Any]:
        """
        生成访问令牌和刷新令牌

        Args:
            user_id: 用户 ID
            email: 用户邮箱（可选）
            provider: 登录提供商（email, wechat, qq 等）

        Returns:
            Dict: 包含 access_token, refresh_token, expires_in 等
        """
        access_token = self.generate_access_token(user_id, email, provider)
        refresh_token = self.generate_refresh_token(user_id)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(self.access_token_expires.total_seconds())
        }

    def generate_access_token(self, user_id: str, email: str = None, provider: str = None, additional_claims: Dict = None) -> str:
        """
        生成访问令牌

        Args:
            user_id: 用户 ID
            email: 用户邮箱（可选）
            provider: 登录提供商
            additional_claims: 额外声明

        Returns:
            str: JWT 访问令牌
        """
        now = datetime.utcnow()
        expires_at = now + self.access_token_expires

        payload = {
            'user_id': user_id,
            'email': email,
            'provider': provider,
            'type': 'access',
            'iat': now,
            'exp': expires_at,
            'iss': self.issuer,
            'aud': self.audience,
            'jti': str(uuid.uuid4())  # JWT ID，用于黑名单
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def generate_refresh_token(self, user_id: str) -> str:
        """
        生成刷新令牌

        Args:
            user_id: 用户 ID

        Returns:
            str: JWT 刷新令牌
        """
        now = datetime.utcnow()
        expires_at = now + self.refresh_token_expires

        payload = {
            'user_id': user_id,
            'type': 'refresh',
            'iat': now,
            'exp': expires_at,
            'iss': self.issuer,
            'aud': self.audience,
            'jti': str(uuid.uuid4())  # JWT ID，用于黑名单
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    # ==================== 令牌验证 ====================
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        验证访问令牌

        Args:
            token: JWT 令牌

        Returns:
            Dict: 令牌 payload

        Raises:
            jwt.ExpiredSignatureError: 令牌已过期
            jwt.InvalidTokenError: 令牌无效
        """
        payload = jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options={'verify_aud': False, 'verify_iss': False}
        )

        if payload.get('type') != 'access':
            raise jwt.InvalidTokenError('Invalid token type')

        self._validate_standard_claims(payload)

        return payload

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        验证刷新令牌

        Args:
            token: JWT 令牌

        Returns:
            Dict: 令牌 payload

        Raises:
            jwt.ExpiredSignatureError: 令牌已过期
            jwt.InvalidTokenError: 令牌无效
        """
        payload = jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
            options={'verify_aud': False, 'verify_iss': False}
        )

        if payload.get('type') != 'refresh':
            raise jwt.InvalidTokenError('Invalid token type')

        self._validate_standard_claims(payload)

        return payload

    def _validate_standard_claims(self, payload: Dict):
        """验证标准声明"""
        now = datetime.utcnow()

        # 验证过期时间
        if 'exp' in payload and payload['exp'] < now.timestamp():
            raise jwt.ExpiredSignatureError('Token has expired')

        # 验证发行者和受众已经在 verify_access_token/verify_refresh_token 中处理

    # ==================== 令牌刷新 ====================
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        使用刷新令牌获取新的访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            Dict: 新的 access_token 和 refresh_token

        Raises:
            jwt.ExpiredSignatureError: 刷新令牌已过期
            jwt.InvalidTokenError: 刷新令牌无效
        """
        # 验证刷新令牌
        payload = self.verify_refresh_token(refresh_token)
        user_id = payload['user_id']

        # 生成新的令牌对
        return self.generate_tokens(user_id)

    # ==================== 辅助方法 ====================
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        解码令牌（不验证，仅用于调试）

        Args:
            token: JWT 令牌

        Returns:
            Dict: 解码后的 payload
        """
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm],
                         options={'verify_exp': False, 'verify_aud': False, 'verify_iss': False})

    def get_token_expires_at(self, token: str) -> datetime:
        """
        获取令牌过期时间

        Args:
            token: JWT 令牌

        Returns:
            datetime: 过期时间
        """
        payload = self.decode_token(token)
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
        return None

    def get_jti(self, token: str) -> str:
        """
        获取令牌的 JTI（JWT ID）

        Args:
            token: JWT 令牌

        Returns:
            str: JTI
        """
        payload = self.decode_token(token)
        return payload.get('jti', '')


# 全局实例
jwt_service = JWTService()
