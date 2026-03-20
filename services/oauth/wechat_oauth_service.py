"""
微信 OAuth2.0 服务类
实现微信网站应用扫码登录功能
"""
import requests
from typing import Dict, Any
from urllib.parse import urlencode
import logging

from .base_oauth_service import BaseOAuthService

logger = logging.getLogger(__name__)


class WeChatOAuthService(BaseOAuthService):
    """
    微信 OAuth2.0 服务类

    微信开放平台文档：https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/Wechat_Login.html
    """

    PROVIDER_NAME = 'wechat'

    # 微信 OAuth2.0 端点
    AUTH_URL = 'https://open.weixin.qq.com/connect/qrconnect'
    TOKEN_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'
    USER_INFO_URL = 'https://api.weixin.qq.com/sns/userinfo'
    TOKEN_CHECK_URL = 'https://api.weixin.qq.com/sns/auth'

    def _initialize(self):
        """初始化微信 OAuth 配置"""
        if self._initialized:
            return

        self.app_id = self._get_config('WECHAT_OAUTH_APP_ID')
        self.app_secret = self._get_config('WECHAT_OAUTH_APP_SECRET')
        self.redirect_uri = self._get_config('WECHAT_OAUTH_REDIRECT_URI')
        self.scope = self._get_config('WECHAT_OAUTH_SCOPE', 'snsapi_login')

        # 验证配置
        if not self.app_id or not self.app_secret:
            logger.warning("WeChat OAuth credentials not configured")
        else:
            self._initialized = True

    def get_authorization_url(self, state: str) -> str:
        """
        获取微信授权 URL（生成二维码）

        Args:
            state: CSRF 防护参数

        Returns:
            str: 微信授权页面 URL
        """
        params = {
            'appid': self.app_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': self.scope,
            'state': state
        }

        # 微信特殊格式：#wechat_redirect 必须附加在 URL 末尾
        base_url = f"{self.AUTH_URL}?{urlencode(params)}"
        return f"{base_url}#wechat_redirect"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        用授权码换取访问令牌

        Args:
            code: 授权码

        Returns:
            Dict: 包含 access_token, expires_in, refresh_token, openid, unionid 等

        Raises:
            Exception: 当 API 调用失败时
        """
        params = {
            'appid': self.app_id,
            'secret': self.app_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }

        try:
            response = requests.get(self.TOKEN_URL, params=params, timeout=30)

            if response.status_code != 200:
                raise Exception(f"WeChat token API error: {response.status_code}")

            result = response.json()

            # 检查错误
            if 'errcode' in result and result['errcode'] != 0:
                error_msg = result.get('errmsg', 'Unknown error')
                raise Exception(f"WeChat OAuth error: {error_msg}")

            # 成功响应
            # {
            #     "access_token": "ACCESS_TOKEN",
            #     "expires_in": 7200,
            #     "refresh_token": "REFRESH_TOKEN",
            #     "openid": "OPENID",
            #     "scope": "snsapi_login",
            #     "unionid": "UNIONID"  // 只有当应用在微信开放平台账号下时才有
            # }

            return {
                'access_token': result.get('access_token'),
                'expires_in': result.get('expires_in', 7200),
                'refresh_token': result.get('refresh_token'),
                'openid': result.get('openid'),
                'unionid': result.get('unionid'),
                'scope': result.get('scope')
            }

        except requests.RequestException as e:
            logger.error(f"WeChat token request failed: {e}")
            raise Exception(f"Failed to exchange code for token: {str(e)}")

    def get_user_info(self, access_token: str, openid: str) -> Dict[str, Any]:
        """
        获取微信用户信息

        Args:
            access_token: 访问令牌
            openid: 用户 openid

        Returns:
            Dict: 用户信息

        Raises:
            Exception: 当 API 调用失败时
        """
        params = {
            'access_token': access_token,
            'openid': openid,
            'lang': 'zh_CN'
        }

        try:
            response = requests.get(self.USER_INFO_URL, params=params, timeout=30)

            if response.status_code != 200:
                raise Exception(f"WeChat user info API error: {response.status_code}")

            result = response.json()

            # 检查错误
            if 'errcode' in result and result['errcode'] != 0:
                error_msg = result.get('errmsg', 'Unknown error')
                raise Exception(f"WeChat user info error: {error_msg}")

            # 成功响应
            # {
            #     "openid": "OPENID",
            #     "nickname": "NICKNAME",
            #     "sex": 1,  // 1=男，2=女，0=未知
            #     "province": "PROVINCE",
            #     "city": "CITY",
            #     "country": "COUNTRY",
            #     "headimgurl": "HEADIMGURL",
            #     "privilege": [],
            #     "unionid": "UNIONID"
            # }

            sex_mapping = {1: 'male', 2: 'female', 0: 'unknown'}

            return {
                'openid': result.get('openid'),
                'nickname': result.get('nickname', '微信用户'),
                'sex': sex_mapping.get(result.get('sex', 0), 'unknown'),
                'province': result.get('province', ''),
                'city': result.get('city', ''),
                'country': result.get('country', 'China'),
                'avatar_url': result.get('headimgurl', ''),
                'unionid': result.get('unionid'),
                'raw_data': result
            }

        except requests.RequestException as e:
            logger.error(f"WeChat user info request failed: {e}")
            raise Exception(f"Failed to get user info: {str(e)}")

    def check_token(self, access_token: str, openid: str) -> bool:
        """
        检查访问令牌是否有效

        Args:
            access_token: 访问令牌
            openid: 用户 openid

        Returns:
            bool: 是否有效
        """
        params = {
            'access_token': access_token,
            'openid': openid
        }

        try:
            response = requests.get(self.TOKEN_CHECK_URL, params=params, timeout=30)

            if response.status_code != 200:
                return False

            result = response.json()

            # 成功响应：{"errcode":0,"errmsg":"ok"}
            return result.get('errcode', -1) == 0

        except requests.RequestException:
            logger.error("WeChat token check failed")
            return False

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            Dict: 新的令牌信息
        """
        params = {
            'appid': self.app_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }

        try:
            response = requests.get(self.TOKEN_URL, params=params, timeout=30)

            if response.status_code != 200:
                raise Exception(f"WeChat refresh API error: {response.status_code}")

            result = response.json()

            if 'errcode' in result and result['errcode'] != 0:
                error_msg = result.get('errmsg', 'Unknown error')
                raise Exception(f"WeChat token refresh error: {error_msg}")

            return {
                'access_token': result.get('access_token'),
                'expires_in': result.get('expires_in', 7200),
                'refresh_token': result.get('refresh_token'),
                'openid': result.get('openid'),
                'scope': result.get('scope')
            }

        except requests.RequestException as e:
            logger.error(f"WeChat token refresh failed: {e}")
            raise Exception(f"Failed to refresh token: {str(e)}")


# 全局实例
wechat_oauth = WeChatOAuthService()
