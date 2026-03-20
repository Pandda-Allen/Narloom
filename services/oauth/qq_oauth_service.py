"""
QQ OAuth2.0 服务类
实现 QQ 网站应用登录功能
"""
import requests
import json
from typing import Dict, Any
from urllib.parse import urlencode, parse_qs
import logging

from .base_oauth_service import BaseOAuthService

logger = logging.getLogger(__name__)


class QQOAuthService(BaseOAuthService):
    """
    QQ OAuth2.0 服务类

    QQ 互联文档：https://wiki.connect.qq.com/oauth2-0%E7%AE%80%E4%BB%8B
    """

    PROVIDER_NAME = 'qq'

    # QQ OAuth2.0 端点
    AUTH_URL = 'https://graph.qq.com/oauth2.0/authorize'
    TOKEN_URL = 'https://graph.qq.com/oauth2.0/token'
    OPENID_URL = 'https://graph.qq.com/oauth2.0/me'
    USER_INFO_URL = 'https://graph.qq.com/user/get_user_info'

    def _initialize(self):
        """初始化 QQ OAuth 配置"""
        if self._initialized:
            return

        self.app_id = self._get_config('QQ_OAUTH_APP_ID')
        self.app_key = self._get_config('QQ_OAUTH_APP_KEY')
        self.redirect_uri = self._get_config('QQ_OAUTH_REDIRECT_URI')
        self.scope = self._get_config('QQ_OAUTH_SCOPE', 'get_user_info')

        # 验证配置
        if not self.app_id or not self.app_key:
            logger.warning("QQ OAuth credentials not configured")
        else:
            self._initialized = True

    def get_authorization_url(self, state: str) -> str:
        """
        获取 QQ 授权 URL

        Args:
            state: CSRF 防护参数

        Returns:
            str: QQ 授权页面 URL
        """
        params = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'scope': self.scope,
        }

        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        用授权码换取访问令牌

        Args:
            code: 授权码

        Returns:
            Dict: 包含 access_token, expires_in, refresh_token, openid 等

        Raises:
            Exception: 当 API 调用失败时

        Note:
            QQ 返回的是 text/plain 格式，不是 JSON
            格式：access_token=xxx&expires_in=7776000&refresh_token=xxx
        """
        params = {
            'grant_type': 'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.app_key,
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        try:
            response = requests.get(self.TOKEN_URL, params=params, timeout=30)

            if response.status_code != 200:
                raise Exception(f"QQ token API error: {response.status_code}")

            # QQ 返回的是 URL 编码格式，不是 JSON
            # 可能包含 callback 前缀，需要处理
            text = response.text

            # 处理 JSONP 回调格式：callback( {...} );
            if text.startswith('callback('):
                text = text[9:-2]  # 去掉 callback( 和 );

            # 解析 URL 编码格式
            token_data = parse_qs(text)

            # 检查错误
            if 'error' in token_data:
                error = token_data['error'][0]
                error_description = token_data.get('error_description', ['Unknown error'])[0]
                raise Exception(f"QQ OAuth error: {error_description}")

            # 成功响应
            # access_token=ACCESS_TOKEN&expires_in=7776000&refresh_token=REFRESH_TOKEN
            return {
                'access_token': token_data.get('access_token', [''])[0],
                'expires_in': int(token_data.get('expires_in', ['7776000'])[0]),
                'refresh_token': token_data.get('refresh_token', [''])[0],
            }

        except requests.RequestException as e:
            logger.error(f"QQ token request failed: {e}")
            raise Exception(f"Failed to exchange code for token: {str(e)}")

    def get_openid(self, access_token: str) -> str:
        """
        获取用户 OpenID

        Args:
            access_token: 访问令牌

        Returns:
            str: 用户 OpenID

        Raises:
            Exception: 当 API 调用失败时

        Note:
            QQ 返回格式：callback({"client_id":"xxx","openid":"xxx"});
        """
        params = {
            'access_token': access_token,
            'fmt': 'json'  # 请求 JSON 格式
        }

        try:
            response = requests.get(self.OPENID_URL, params=params, timeout=30)

            if response.status_code != 200:
                raise Exception(f"QQ openid API error: {response.status_code}")

            text = response.text

            # 处理 JSONP 回调格式
            if text.startswith('callback('):
                text = text[9:-1]  # 去掉 callback( 和 )

            result = json.loads(text)

            if 'error' in result:
                error = result.get('error', 'Unknown error')
                error_description = result.get('error_description', str(error))
                raise Exception(f"QQ OpenID error: {error_description}")

            return result.get('openid', '')

        except requests.RequestException as e:
            logger.error(f"QQ openid request failed: {e}")
            raise Exception(f"Failed to get openid: {str(e)}")

    def get_user_info(self, access_token: str, openid: str = None) -> Dict[str, Any]:
        """
        获取 QQ 用户信息

        Args:
            access_token: 访问令牌
            openid: 用户 openid（可选，会从 token 中获取）

        Returns:
            Dict: 用户信息

        Raises:
            Exception: 当 API 调用失败时

        Note:
            如果未提供 openid，会自动调用 get_openid 获取
        """
        # 如果没有 openid，先获取
        if not openid:
            openid = self.get_openid(access_token)

        params = {
            'access_token': access_token,
            'oauth_consumer_key': self.app_id,
            'openid': openid
        }

        try:
            response = requests.get(self.USER_INFO_URL, params=params, timeout=30)

            if response.status_code != 200:
                raise Exception(f"QQ user info API error: {response.status_code}")

            result = response.json()

            # 检查错误
            if result.get('ret', 0) != 0:
                error_msg = result.get('msg', 'Unknown error')
                raise Exception(f"QQ user info error: {error_msg}")

            # 成功响应
            # {
            #     "ret": 0,
            #     "nickname": "NICKNAME",
            #     "gender": "男",
            #     "province": "PROVINCE",
            #     "city": "CITY",
            #     "year": "1990",
            #     "avatar": "AVATAR_URL"
            # }

            gender_mapping = {
                '男': 'male',
                '女': 'female',
                '': 'unknown'
            }

            return {
                'openid': openid,
                'nickname': result.get('nickname', 'QQ 用户'),
                'sex': gender_mapping.get(result.get('gender', ''), 'unknown'),
                'province': result.get('province', ''),
                'city': result.get('city', ''),
                'avatar_url': result.get('figureurl_qq_2', result.get('figureurl_qq_1', result.get('avatar', ''))),
                'year': result.get('year', ''),
                'raw_data': result
            }

        except requests.RequestException as e:
            logger.error(f"QQ user info request failed: {e}")
            raise Exception(f"Failed to get user info: {str(e)}")

    def get_user_info_simple(self, access_token: str, openid: str) -> Dict[str, Any]:
        """
        获取 QQ 用户信息（简化版，使用 REST API）

        Args:
            access_token: 访问令牌
            openid: 用户 openid

        Returns:
            Dict: 用户信息
        """
        return self.get_user_info(access_token, openid)


# 全局实例
qq_oauth = QQOAuthService()
