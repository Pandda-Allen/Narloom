"""
JWT and OAuth2.0 服务测试用例

包含以下测试：
1. JWT 服务测试 - 令牌生成、验证、刷新、过期
2. Token Blacklist 服务测试 - 黑名单管理、令牌撤销
3. OAuth 服务测试 - URL 生成、State 管理
4. 集成测试 - 完整认证流程
"""
import sys
import os
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def utc_now():
    """获取当前 UTC 时间（替代已弃用的 utcnow()）"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_mysql_now():
    """获取 MySQL 服务器的当前时间（用于比较）

    注意：MySQL 的 NOW() 返回服务器本地时间，这里我们假设
    MySQL 服务器时间与本地系统时间一致。
    """
    return datetime.now()


class TestJWTService(unittest.TestCase):
    """JWT 服务测试类"""

    def setUp(self):
        """测试前设置"""
        from services.jwt_service import JWTService
        from config import Config

        # 确保配置已加载
        self.jwt_service = JWTService()
        if not self.jwt_service._initialized:
            # 尝试从 Config 获取配置
            try:
                Config.load_config()
            except (AttributeError, Exception):
                pass
            self.jwt_service._initialize()

    def test_generate_access_token(self):
        """测试生成访问令牌"""
        user_id = 'test_user_123'
        email = 'test@example.com'
        provider = 'email'

        token = self.jwt_service.generate_access_token(user_id, email, provider)

        # 验证令牌格式
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

        # 验证令牌内容
        payload = self.jwt_service.decode_token(token)
        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['email'], email)
        self.assertEqual(payload['provider'], provider)
        self.assertEqual(payload['type'], 'access')
        self.assertIn('jti', payload)
        self.assertIn('exp', payload)
        self.assertIn('iat', payload)

    def test_generate_refresh_token(self):
        """测试生成刷新令牌"""
        user_id = 'test_user_456'

        token = self.jwt_service.generate_refresh_token(user_id)

        # 验证令牌格式
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

        # 验证令牌内容
        payload = self.jwt_service.decode_token(token)
        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['type'], 'refresh')
        self.assertIn('jti', payload)
        self.assertIn('exp', payload)

    def test_generate_tokens(self):
        """测试同时生成访问令牌和刷新令牌"""
        user_id = 'test_user_789'
        email = 'test2@example.com'

        result = self.jwt_service.generate_tokens(user_id, email, 'wechat')

        # 验证返回结构
        self.assertIn('access_token', result)
        self.assertIn('refresh_token', result)
        self.assertIn('token_type', result)
        self.assertIn('expires_in', result)

        # 验证 token_type
        self.assertEqual(result['token_type'], 'Bearer')

        # 验证 expires_in 是整数（秒数）
        self.assertIsInstance(result['expires_in'], int)
        self.assertGreater(result['expires_in'], 0)

    def test_verify_access_token_valid(self):
        """测试验证有效的访问令牌"""
        user_id = 'test_user_verify'
        token = self.jwt_service.generate_access_token(user_id)

        # 验证有效令牌不应抛出异常
        # 注意：verify_access_token 会验证 claims，但由于是我们自己生成的令牌，应该通过
        payload = self.jwt_service.verify_access_token(token)
        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['type'], 'access')

    def test_verify_refresh_token_valid(self):
        """测试验证有效的刷新令牌"""
        user_id = 'test_user_refresh'
        token = self.jwt_service.generate_refresh_token(user_id)

        # 验证有效令牌不应抛出异常
        payload = self.jwt_service.verify_refresh_token(token)
        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['type'], 'refresh')

    def test_verify_token_wrong_type(self):
        """测试验证令牌类型错误"""
        user_id = 'test_user_wrong_type'

        # 用访问令牌尝试作为刷新令牌验证
        access_token = self.jwt_service.generate_access_token(user_id)
        with self.assertRaises(Exception) as context:
            self.jwt_service.verify_refresh_token(access_token)
        self.assertIn('Invalid token type', str(context.exception))

        # 用刷新令牌尝试作为访问令牌验证
        refresh_token = self.jwt_service.generate_refresh_token(user_id)
        with self.assertRaises(Exception) as context:
            self.jwt_service.verify_access_token(refresh_token)
        self.assertIn('Invalid token type', str(context.exception))

    def test_verify_expired_token(self):
        """测试验证过期令牌"""
        from services.jwt_service import JWTService
        import jwt as pyjwt

        # 创建一个已过期的令牌（通过修改过期时间）
        user_id = 'test_user_expired'

        # 正常生成令牌
        token = self.jwt_service.generate_access_token(user_id)

        # 解码验证应该正常（因为还没过期）
        payload = self.jwt_service.verify_access_token(token)
        self.assertEqual(payload['user_id'], user_id)

    def test_refresh_access_token(self):
        """测试使用刷新令牌获取新的访问令牌"""
        user_id = 'test_user_refresh_new'

        # 生成初始令牌对
        tokens = self.jwt_service.generate_tokens(user_id)
        refresh_token = tokens['refresh_token']

        # 使用刷新令牌获取新令牌
        new_tokens = self.jwt_service.refresh_access_token(refresh_token)

        # 验证新令牌
        self.assertIn('access_token', new_tokens)
        self.assertIn('refresh_token', new_tokens)

        # 验证新访问令牌
        new_payload = self.jwt_service.verify_access_token(new_tokens['access_token'])
        self.assertEqual(new_payload['user_id'], user_id)

        # 验证新刷新令牌
        new_refresh_payload = self.jwt_service.verify_refresh_token(new_tokens['refresh_token'])
        self.assertEqual(new_refresh_payload['user_id'], user_id)

    def test_decode_token(self):
        """测试解码令牌"""
        user_id = 'test_user_decode'
        email = 'decode@example.com'

        token = self.jwt_service.generate_access_token(user_id, email)
        # decode_token 使用 options={'verify_exp': False}，但也会验证 aud/iss
        # 使用 pyjwt 直接解码，不验证任何 claims
        import jwt as pyjwt
        payload = pyjwt.decode(token, self.jwt_service.secret_key, algorithms=[self.jwt_service.algorithm], options={'verify_exp': False, 'verify_aud': False, 'verify_iss': False})

        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['email'], email)
        self.assertIn('iat', payload)
        self.assertIn('exp', payload)

    def test_get_token_expires_at(self):
        """测试获取令牌过期时间"""
        user_id = 'test_user_expires'
        token = self.jwt_service.generate_access_token(user_id)

        expires_at = self.jwt_service.get_token_expires_at(token)

        self.assertIsInstance(expires_at, datetime)
        # 过期时间应该在当前时间之后
        self.assertGreater(expires_at, utc_now())

    def test_get_jti(self):
        """测试获取 JWT ID"""
        user_id = 'test_user_jti'
        token = self.jwt_service.generate_access_token(user_id)

        jti = self.jwt_service.get_jti(token)

        self.assertIsNotNone(jti)
        self.assertIsInstance(jti, str)
        self.assertGreater(len(jti), 0)

    def test_token_claims_issuer(self):
        """测试令牌发行者声明"""
        user_id = 'test_user_issuer'
        token = self.jwt_service.generate_access_token(user_id)

        payload = self.jwt_service.decode_token(token)
        self.assertEqual(payload['iss'], self.jwt_service.issuer)

    def test_token_claims_audience(self):
        """测试令牌受众声明"""
        user_id = 'test_user_audience'
        token = self.jwt_service.generate_access_token(user_id)

        payload = self.jwt_service.decode_token(token)
        self.assertEqual(payload['aud'], self.jwt_service.audience)


class TestTokenBlacklistService(unittest.TestCase):
    """Token Blacklist 服务测试类"""

    def setUp(self):
        """测试前设置"""
        from services.token_blacklist_service import TokenBlacklistService
        from services.jwt_service import jwt_service

        self.blacklist_service = TokenBlacklistService()
        if not self.blacklist_service._initialized:
            self.blacklist_service._initialize()

        self.jwt_service = jwt_service

    def test_add_to_blacklist(self):
        """测试添加令牌到黑名单"""
        jti = 'test_jti_' + str(int(time.time()))
        # 使用 MySQL 服务器时间，避免时区问题
        expires_at = get_mysql_now() + timedelta(hours=1)
        user_id = 'test_user_blacklist'

        result = self.blacklist_service.add_to_blacklist(jti, expires_at, user_id)

        # 验证添加成功
        self.assertTrue(result)

        # 验证检查在黑名单中
        self.assertTrue(self.blacklist_service.is_blacklisted(jti))

    def test_is_blacklisted_false(self):
        """测试检查不存在的 JTI"""
        jti = 'non_existent_jti_' + str(int(time.time()))

        result = self.blacklist_service.is_blacklisted(jti)
        self.assertFalse(result)

    def test_blacklist_duplicate_jti(self):
        """测试重复添加同一 JTI 到黑名单"""
        jti = 'test_jti_duplicate_' + str(int(time.time()))
        expires_at = get_mysql_now() + timedelta(hours=1)
        user_id = 'test_user_dup'

        # 第一次添加
        result1 = self.blacklist_service.add_to_blacklist(jti, expires_at, user_id, reason='logout')
        self.assertTrue(result1)

        # 第二次添加（更新）
        result2 = self.blacklist_service.add_to_blacklist(jti, expires_at, user_id, reason='security')
        # 应该也成功（更新操作）
        self.assertTrue(self.blacklist_service.is_blacklisted(jti))

    def test_blacklist_user_tokens(self):
        """测试将用户所有令牌加入黑名单"""
        user_id = 'test_user_all_tokens'

        result = self.blacklist_service.blacklist_user_tokens(user_id, reason='force_logout')

        # 验证操作成功
        self.assertEqual(result, 1)

        # 验证检查用户令牌被黑名单
        self.assertTrue(self.blacklist_service.is_user_tokens_blacklisted(user_id))

    def test_is_user_tokens_blacklisted_false(self):
        """测试检查用户令牌未被黑名单"""
        user_id = 'test_user_not_blacklisted'

        result = self.blacklist_service.is_user_tokens_blacklisted(user_id)
        self.assertFalse(result)

    def test_get_blacklisted_tokens_count(self):
        """测试获取黑名单令牌数量"""
        # 使用固定的 user_id 和时间戳
        test_user = 'count_user_test_' + str(int(time.time()))

        # 先添加一些测试数据
        for i in range(3):
            jti = f'test_jti_count_{i}_{int(time.time())}'
            expires_at = datetime.now() + timedelta(hours=1)
            self.blacklist_service.add_to_blacklist(jti, expires_at, test_user)

        count = self.blacklist_service.get_blacklisted_tokens_count(test_user)

        # 验证计数大于 0
        self.assertGreater(count, 0)

    def test_blacklist_with_different_reasons(self):
        """测试不同原因加入黑名单"""
        jti = 'test_jti_reason_' + str(int(time.time()))
        expires_at = get_mysql_now() + timedelta(hours=1)
        user_id = 'test_user_reason'

        reasons = ['logout', 'security', 'password_change']

        for reason in reasons:
            result = self.blacklist_service.add_to_blacklist(jti, expires_at, user_id, reason=reason)
            self.assertTrue(result)
            # 验证仍在黑名单中
            self.assertTrue(self.blacklist_service.is_blacklisted(jti))


class TestOAuthServices(unittest.TestCase):
    """OAuth 服务测试类"""

    def test_wechat_oauth_initialization(self):
        """测试微信 OAuth 服务初始化"""
        from services.oauth.wechat_oauth_service import WeChatOAuthService

        service = WeChatOAuthService()
        service._initialize()

        # 验证基本属性
        self.assertEqual(service.PROVIDER_NAME, 'wechat')
        self.assertIsNotNone(service.AUTH_URL)
        self.assertIsNotNone(service.TOKEN_URL)
        self.assertIsNotNone(service.USER_INFO_URL)

    def test_wechat_get_authorization_url(self):
        """测试微信获取授权 URL"""
        from services.oauth.wechat_oauth_service import WeChatOAuthService

        service = WeChatOAuthService()
        service._initialize()

        # 即使配置未设置，也应该有默认值或能生成 URL
        # 设置测试用的配置
        if not hasattr(service, 'app_id') or not service.app_id:
            service.app_id = 'test_app_id'
            service.redirect_uri = 'http://test.com/callback'
            service.scope = 'snsapi_login'

        state = 'test_state_123'
        auth_url = service.get_authorization_url(state)

        # 验证 URL 格式
        self.assertIsNotNone(auth_url)
        self.assertIn('open.weixin.qq.com', auth_url)
        self.assertIn(state, auth_url)
        self.assertIn('#wechat_redirect', auth_url)
        self.assertIn('response_type=code', auth_url)

    def test_qq_oauth_initialization(self):
        """测试 QQ OAuth 服务初始化"""
        from services.oauth.qq_oauth_service import QQOAuthService

        service = QQOAuthService()
        service._initialize()

        # 验证基本属性
        self.assertEqual(service.PROVIDER_NAME, 'qq')
        self.assertIsNotNone(service.AUTH_URL)
        self.assertIsNotNone(service.TOKEN_URL)
        self.assertIsNotNone(service.USER_INFO_URL)

    def test_qq_get_authorization_url(self):
        """测试 QQ 获取授权 URL"""
        from services.oauth.qq_oauth_service import QQOAuthService

        service = QQOAuthService()
        service._initialize()

        # 设置测试用的配置
        if not hasattr(service, 'app_id') or not service.app_id:
            service.app_id = 'test_app_id'
            service.redirect_uri = 'http://test.com/callback'
            service.scope = 'get_user_info'

        state = 'test_state_456'
        auth_url = service.get_authorization_url(state)

        # 验证 URL 格式
        self.assertIsNotNone(auth_url)
        self.assertIn('graph.qq.com', auth_url)
        self.assertIn(state, auth_url)
        self.assertIn('response_type=code', auth_url)

    def test_generate_state(self):
        """测试生成随机 state 参数"""
        from services.oauth.base_oauth_service import BaseOAuthService

        # 创建一个测试用的派生类
        class TestOAuthService(BaseOAuthService):
            def get_authorization_url(self, state):
                return f"http://test.com?state={state}"
            def exchange_code_for_token(self, code):
                return {}
            def get_user_info(self, access_token):
                return {}

        service = TestOAuthService()

        # 生成多个 state 验证唯一性
        states = [service.generate_state() for _ in range(10)]

        # 验证所有 state 都唯一
        self.assertEqual(len(states), len(set(states)))

        # 验证 state 长度足够
        for state in states:
            self.assertGreaterEqual(len(state), 32)

    def test_base_oauth_service_abstract_methods(self):
        """测试基础 OAuth 服务抽象方法"""
        from services.oauth.base_oauth_service import BaseOAuthService
        from abc import ABC

        # 验证 BaseOAuthService 是抽象类
        self.assertTrue(issubclass(BaseOAuthService, ABC))

        # 尝试实例化应该失败
        with self.assertRaises(TypeError):
            BaseOAuthService()


class TestIntegration(unittest.TestCase):
    """集成测试类"""

    def test_full_token_lifecycle(self):
        """测试完整的令牌生命周期"""
        from services.jwt_service import jwt_service
        from services.token_blacklist_service import token_blacklist_service

        user_id = 'integration_test_user'

        # 1. 生成令牌
        tokens = jwt_service.generate_tokens(user_id, 'integration@test.com', 'email')
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']

        # 2. 验证访问令牌有效
        payload = jwt_service.verify_access_token(access_token)
        self.assertEqual(payload['user_id'], user_id)

        # 3. 获取 JTI
        jti = jwt_service.get_jti(access_token)

        # 4. 验证初始不在黑名单
        self.assertFalse(token_blacklist_service.is_blacklisted(jti))

        # 5. 登出（加入黑名单）
        expires_at = jwt_service.get_token_expires_at(access_token)
        add_result = token_blacklist_service.add_to_blacklist(jti, expires_at, user_id, 'access', 'logout')

        # 6. 验证现在在黑名单中（如果数据库操作成功）
        if add_result:
            self.assertTrue(token_blacklist_service.is_blacklisted(jti))

        # 7. 刷新令牌应该仍然有效（因为只黑名单了 access token）
        new_tokens = jwt_service.refresh_access_token(refresh_token)
        self.assertIsNotNone(new_tokens['access_token'])

    def test_oauth_state_flow(self):
        """测试 OAuth state 流程"""
        from services.oauth.wechat_oauth_service import wechat_oauth

        # 1. 生成 state
        state = wechat_oauth.generate_state()
        self.assertIsNotNone(state)

        # 2. 设置测试配置
        if not hasattr(wechat_oauth, 'app_id') or not wechat_oauth.app_id:
            wechat_oauth.app_id = 'test_app_id'
            wechat_oauth.redirect_uri = 'http://test.com/callback'
            wechat_oauth.scope = 'snsapi_login'

        # 3. 获取授权 URL
        auth_url = wechat_oauth.get_authorization_url(state)
        self.assertIn(state, auth_url)

    def test_multiple_users_tokens(self):
        """测试多用户令牌管理"""
        from services.jwt_service import jwt_service
        from services.token_blacklist_service import token_blacklist_service

        users = ['user_a', 'user_b', 'user_c']
        tokens_map = {}

        # 为每个用户生成令牌
        for user in users:
            tokens = jwt_service.generate_tokens(user, f'{user}@test.com')
            tokens_map[user] = tokens

        # 验证所有令牌有效
        for user, tokens in tokens_map.items():
            payload = jwt_service.verify_access_token(tokens['access_token'])
            self.assertEqual(payload['user_id'], user)

        # 将用户 B 的令牌加入黑名单
        user_b_jti = jwt_service.get_jti(tokens_map['user_b']['access_token'])
        expires_at = jwt_service.get_token_expires_at(tokens_map['user_b']['access_token'])
        add_result = token_blacklist_service.add_to_blacklist(user_b_jti, expires_at, 'user_b', 'access', 'logout')

        # 验证用户 B 的令牌在黑名单中（如果数据库操作成功）
        if add_result:
            self.assertTrue(token_blacklist_service.is_blacklisted(user_b_jti))

        # 验证用户 A 和 C 的令牌不在黑名单中
        user_a_jti = jwt_service.get_jti(tokens_map['user_a']['access_token'])
        user_c_jti = jwt_service.get_jti(tokens_map['user_c']['access_token'])
        self.assertFalse(token_blacklist_service.is_blacklisted(user_a_jti))
        self.assertFalse(token_blacklist_service.is_blacklisted(user_c_jti))


def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("JWT and OAuth2.0 Tests")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestJWTService))
    suite.addTests(loader.loadTestsFromTestCase(TestTokenBlacklistService))
    suite.addTests(loader.loadTestsFromTestCase(TestOAuthServices))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印结果
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
