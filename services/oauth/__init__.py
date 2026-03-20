"""
OAuth2.0 服务包
提供微信、QQ 等第三方登录服务
"""
from .base_oauth_service import BaseOAuthService
from .wechat_oauth_service import WeChatOAuthService
from .qq_oauth_service import QQOAuthService

__all__ = [
    'BaseOAuthService',
    'WeChatOAuthService',
    'QQOAuthService',
]
