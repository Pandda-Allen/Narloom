"""
用户路由模块
整合登录、注册、用户资料管理和删除功能，支持 JWT 和 OAuth2.0
"""
from flask import Blueprint, request, g, current_app
from utils.response_helper import api_response, error_response
from utils.decorators import handle_errors, jwt_required, optional_jwt
from services.mysql_service import mysql_service
from services.mongo_service import MongoService
from services.picture_service import picture_service
from services.jwt_service import jwt_service
from services.token_blacklist_service import token_blacklist_service
import logging

logger = logging.getLogger(__name__)

# ==================== 蓝图定义 ====================
user_bp = Blueprint('user', __name__, url_prefix='/user')

# ==================== 验证辅助函数 ====================
def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    return '@' in email


def validate_password(password: str) -> tuple:
    """
    验证密码强度
    Returns: (is_valid, error_message)
    """
    if len(password) < 6:
        return False, 'Password must be at least 6 characters'
    return True, None


def build_user_response(user: dict) -> dict:
    """构建用户响应数据（不包含密码哈希）"""
    return {
        'user_id': user.get('user_id'),
        'email': user.get('email'),
        'name': user.get('name', ''),
        'bio': user.get('bio', ''),
        'phone': user.get('phone'),
        'avatar_url': user.get('avatar_url'),
        'created_at': user.get('created_at'),
        'last_login_provider': user.get('last_login_provider')
    }


# ==================== 用户注册 ====================
@user_bp.route('/register', methods=['POST'])
@handle_errors
def register():
    """用户注册（邮箱密码方式）"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    bio = data.get('bio', '')

    # 验证必填字段
    if not email or not password:
        return error_response('Email and password are required', 400)

    # 验证邮箱格式
    if not validate_email(email):
        return error_response('Invalid email format', 400)

    # 验证密码强度
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return error_response(error_msg, 400)

    # 注册用户
    user = mysql_service.register_user(email, password, name, bio)

    if user is None:
        return error_response('Email already registered', 409)

    # 生成 JWT 令牌
    tokens = jwt_service.generate_tokens(user['user_id'], user.get('email'), 'email')

    return api_response(
        success=True,
        message='Registration successful',
        data={
            'user': build_user_response(user),
            **tokens
        }
    )


# ==================== 用户登录 ====================
@user_bp.route('/login', methods=['POST'])
@handle_errors
def login():
    """用户登录（邮箱密码方式）"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # 验证必填字段
    if not email or not password:
        return error_response('Email and password are required', 400)

    # 验证邮箱格式
    if not validate_email(email):
        return error_response('Invalid email format', 400)

    try:
        # 使用 MySQL 进行认证
        user = mysql_service.authenticate_user(email, password)

        if user:
            # 更新最后登录时间
            mysql_service.update_user_last_login(user['user_id'], 'email')

            # 生成 JWT 令牌
            tokens = jwt_service.generate_tokens(user['user_id'], user.get('email'), 'email')

            return api_response(
                success=True,
                message='Login successful',
                data={
                    'user': build_user_response(user),
                    **tokens
                }
            )
        else:
            return error_response('Invalid credentials', 401)

    except Exception as e:
        logger.error(f"Login error for email {email}: {type(e).__name__}")
        return error_response('Invalid credentials', 401)


# ==================== JWT 令牌刷新 ====================
@user_bp.route('/refresh', methods=['POST'])
@handle_errors
def refresh_token():
    """
    刷新访问令牌
    使用刷新令牌获取新的访问令牌和刷新令牌
    """
    data = request.get_json()
    if not data:
        return error_response('Request body must be JSON', 400)

    refresh_token_str = data.get('refresh_token')

    if not refresh_token_str:
        return error_response('Refresh token required', 400)

    try:
        # 验证刷新令牌
        payload = jwt_service.verify_refresh_token(refresh_token_str)
        user_id = payload['user_id']

        # 检查用户的刷新令牌是否被撤销
        if token_blacklist_service.is_user_tokens_blacklisted(user_id):
            return error_response('Refresh token has been revoked', 401)

        # 生成新的令牌对
        new_tokens = jwt_service.generate_tokens(user_id)

        return api_response(
            success=True,
            message='Token refreshed successfully',
            data=new_tokens
        )

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return error_response(f'Invalid refresh token: {str(e)}', 401)


# ==================== 用户登出 ====================
@user_bp.route('/logout', methods=['POST'])
@jwt_required
@handle_errors
def logout():
    """
    用户登出
    将当前访问令牌加入黑名单，可选地也使刷新令牌失效
    """
    data = request.get_json() or {}
    blacklist_refresh = data.get('refresh', False)

    user_id = g.current_user_id
    token_payload = g.current_token_payload
    jti = token_payload.get('jti', '')

    # 将 access token 加入黑名单
    from datetime import datetime
    expires_at = jwt_service.get_token_expires_at(g.current_token)

    token_blacklist_service.add_to_blacklist(
        jti=jti,
        expires_at=expires_at,
        user_id=user_id,
        token_type='access',
        reason='logout'
    )

    # 可选：将该用户的所有刷新令牌也加入黑名单
    if blacklist_refresh:
        token_blacklist_service.blacklist_user_tokens(user_id, 'logout')

    return api_response(
        success=True,
        message='Logout successful'
    )


# ==================== 获取用户资料 ====================
@user_bp.route('/<user_id>', methods=['GET'])
@handle_errors
def get_user_profile(user_id: str):
    """获取用户资料"""
    user = mysql_service.fetch_user_by_id(user_id)

    if not user:
        return error_response('User not found', 404)

    return api_response(
        success=True,
        message='User profile fetched successfully',
        data=build_user_response(user)
    )


# ==================== 获取当前用户资料 ====================
@user_bp.route('/me', methods=['GET'])
@jwt_required
@handle_errors
def get_current_user():
    """获取当前登录用户资料"""
    user_id = g.current_user_id

    user = mysql_service.fetch_user_by_id(user_id)

    if not user:
        return error_response('User not found', 404)

    return api_response(
        success=True,
        message='Current user fetched successfully',
        data=build_user_response(user)
    )


# ==================== 用户资料管理 ====================
@user_bp.route('/<user_id>', methods=['PUT'])
@handle_errors
def update_user_profile(user_id: str):
    """更新用户资料"""
    data = request.get_json()

    if data is None:
        return error_response('Request body must be JSON', 400)

    # 构建更新数据
    update_data = {}
    if 'name' in data:
        update_data['name'] = data.get('name')
    if 'bio' in data:
        update_data['bio'] = data.get('bio')
    if 'email' in data:
        update_data['email'] = data.get('email')
    if 'phone' in data:
        update_data['phone'] = data.get('phone')
    if 'avatar_url' in data:
        update_data['avatar_url'] = data.get('avatar_url')

    if not update_data:
        return error_response('No fields to update', 400)

    # 更新用户资料
    updated_user = mysql_service.update_user(user_id, update_data)

    if updated_user:
        return api_response(
            success=True,
            message='User profile updated successfully',
            data=build_user_response(updated_user)
        )
    else:
        return error_response('User not found', 404)


# ==================== OAuth2.0 相关端点 ====================

@user_bp.route('/oauth/wechat/redirect', methods=['GET'])
@handle_errors
def wechat_oauth_redirect():
    """
    获取微信 OAuth 授权 URL
    前端收到 URL 后引导用户跳转到微信授权页面
    """
    from services.oauth.wechat_oauth_service import wechat_oauth

    # 生成 state 参数（CSRF 防护）
    state = wechat_oauth.generate_state()

    # 保存 state 到数据库
    wechat_oauth.save_state(state, 'wechat', 'login')

    # 获取授权 URL
    auth_url = wechat_oauth.get_authorization_url(state)

    return api_response(
        success=True,
        message='WeChat auth URL generated',
        data={'authorization_url': auth_url, 'state': state}
    )


@user_bp.route('/oauth/qq/redirect', methods=['GET'])
@handle_errors
def qq_oauth_redirect():
    """
    获取 QQ OAuth 授权 URL
    前端收到 URL 后引导用户跳转到 QQ 授权页面
    """
    from services.oauth.qq_oauth_service import qq_oauth

    # 生成 state 参数（CSRF 防护）
    state = qq_oauth.generate_state()

    # 保存 state 到数据库
    qq_oauth.save_state(state, 'qq', 'login')

    # 获取授权 URL
    auth_url = qq_oauth.get_authorization_url(state)

    return api_response(
        success=True,
        message='QQ auth URL generated',
        data={'authorization_url': auth_url, 'state': state}
    )


@user_bp.route('/oauth/wechat/callback', methods=['POST'])
@handle_errors
def wechat_oauth_callback():
    """
    微信 OAuth 回调处理
    前端在用户从微信授权页返回后，调用此接口传递 code

    请求体：
    {
        "code": "授权码",
        "state": "CSRF 防护参数"
    }
    """
    from services.oauth.wechat_oauth_service import wechat_oauth

    data = request.get_json()
    if not data:
        return error_response('Request body must be JSON', 400)

    code = data.get('code')
    state = data.get('state')

    if not code or not state:
        return error_response('Missing code or state', 400)

    # 验证 state（CSRF 防护）
    if not wechat_oauth.validate_state(state, 'wechat', 'login'):
        return error_response('Invalid or expired state parameter', 403)

    # 用 code 换取 access_token 和用户信息
    token_data = wechat_oauth.exchange_code_for_token(code)
    openid = token_data['openid']
    unionid = token_data.get('unionid')
    access_token = token_data['access_token']

    # 获取用户信息
    user_info = wechat_oauth.get_user_info(access_token, openid)

    # 查找或创建用户
    user = mysql_service.fetch_user_by_oauth('wechat', openid)

    if not user:
        # 创建新用户
        user = mysql_service.create_oauth_user(
            provider='wechat',
            open_id=openid,
            union_id=unionid,
            provider_data=user_info.get('raw_data'),
            name=user_info.get('nickname', '微信用户'),
            avatar_url=user_info.get('avatar_url')
        )

        if not user:
            return error_response('Failed to create user', 500)
    else:
        # 更新最后登录信息
        mysql_service.update_user_last_login(user['user_id'], 'wechat')

        # 更新 OAuth 令牌
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 7200))
        mysql_service.update_oauth_tokens(
            user['user_id'],
            'wechat',
            access_token=access_token,
            access_token_expires_at=expires_at,
            refresh_token=token_data.get('refresh_token')
        )

    # 生成 JWT
    tokens = jwt_service.generate_tokens(user['user_id'], user.get('email'), 'wechat')

    return api_response(
        success=True,
        message='WeChat login successful',
        data={
            'user': build_user_response(user),
            **tokens
        }
    )


@user_bp.route('/oauth/qq/callback', methods=['POST'])
@handle_errors
def qq_oauth_callback():
    """
    QQ OAuth 回调处理
    前端在用户从 QQ 授权页返回后，调用此接口传递 code

    请求体：
    {
        "code": "授权码",
        "state": "CSRF 防护参数"
    }
    """
    from services.oauth.qq_oauth_service import qq_oauth

    data = request.get_json()
    if not data:
        return error_response('Request body must be JSON', 400)

    code = data.get('code')
    state = data.get('state')

    if not code or not state:
        return error_response('Missing code or state', 400)

    # 验证 state（CSRF 防护）
    if not qq_oauth.validate_state(state, 'qq', 'login'):
        return error_response('Invalid or expired state parameter', 403)

    # 用 code 换取 access_token
    token_data = qq_oauth.exchange_code_for_token(code)
    access_token = token_data['access_token']

    # 获取 openid
    openid = qq_oauth.get_openid(access_token)

    # 获取用户信息
    user_info = qq_oauth.get_user_info(access_token, openid)

    # 查找或创建用户
    user = mysql_service.fetch_user_by_oauth('qq', openid)

    if not user:
        # 创建新用户
        user = mysql_service.create_oauth_user(
            provider='qq',
            open_id=openid,
            provider_data=user_info.get('raw_data'),
            name=user_info.get('nickname', 'QQ 用户'),
            avatar_url=user_info.get('avatar_url')
        )

        if not user:
            return error_response('Failed to create user', 500)
    else:
        # 更新最后登录信息
        mysql_service.update_user_last_login(user['user_id'], 'qq')

        # 更新 OAuth 令牌
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 7776000))
        mysql_service.update_oauth_tokens(
            user['user_id'],
            'qq',
            access_token=access_token,
            access_token_expires_at=expires_at,
            refresh_token=token_data.get('refresh_token')
        )

    # 生成 JWT
    tokens = jwt_service.generate_tokens(user['user_id'], user.get('email'), 'qq')

    return api_response(
        success=True,
        message='QQ login successful',
        data={
            'user': build_user_response(user),
            **tokens
        }
    )


@user_bp.route('/oauth/bind', methods=['POST'])
@jwt_required
@handle_errors
def bind_oauth_account():
    """
    为已登录用户绑定 OAuth 账号
    请求体：
    {
        "provider": "wechat" 或 "qq",
        "code": "授权码"
    }
    """
    from services.oauth.wechat_oauth_service import wechat_oauth
    from services.oauth.qq_oauth_service import qq_oauth

    user_id = g.current_user_id
    data = request.get_json()

    if not data:
        return error_response('Request body must be JSON', 400)

    provider = data.get('provider')
    code = data.get('code')

    if not provider or not code:
        return error_response('provider and code are required', 400)

    if provider not in ['wechat', 'qq']:
        return error_response('Unsupported provider', 400)

    # 获取对应的 OAuth 服务
    oauth_service = wechat_oauth if provider == 'wechat' else qq_oauth

    # 用 code 换取 token 和用户信息
    token_data = oauth_service.exchange_code_for_token(code)
    access_token = token_data['access_token']

    if provider == 'wechat':
        openid = token_data['openid']
        unionid = token_data.get('unionid')
        user_info = oauth_service.get_user_info(access_token, openid)
    else:
        openid = oauth_service.get_openid(access_token)
        user_info = oauth_service.get_user_info(access_token, openid)
        unionid = None

    # 检查是否已绑定
    existing = mysql_service.fetch_user_by_oauth(provider, openid)
    if existing and existing['user_id'] != user_id:
        return error_response(f'This {provider} account is already bound to another user', 409)

    # 绑定 OAuth 账号
    from datetime import datetime, timedelta
    expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 7200))

    success = mysql_service.bind_oauth_account(
        user_id=user_id,
        provider=provider,
        open_id=openid,
        union_id=unionid,
        access_token=access_token,
        access_token_expires_at=expires_at,
        refresh_token=token_data.get('refresh_token'),
        provider_data=user_info.get('raw_data')
    )

    if success:
        return api_response(
            success=True,
            message=f'{provider.capitalize()} account bound successfully'
        )
    else:
        return error_response('Failed to bind OAuth account', 500)


@user_bp.route('/oauth/unbind/<provider>', methods=['POST'])
@jwt_required
@handle_errors
def unbind_oauth_account(provider: str):
    """
    解绑 OAuth 账号
    provider: wechat 或 qq
    """
    user_id = g.current_user_id

    if provider not in ['wechat', 'qq']:
        return error_response('Unsupported provider', 400)

    # 检查是否绑定了该 provider
    accounts = mysql_service.fetch_user_oauth_accounts(user_id)
    provider_accounts = [a for a in accounts if a['provider'] == provider]

    if not provider_accounts:
        return error_response(f'No {provider} account bound', 404)

    # 如果是唯一的登录方式，不允许解绑
    if len(accounts) == 1 and not mysql_service.fetch_user_by_id(user_id).get('password_hash'):
        return error_response('Cannot unbind the only login method', 400)

    # 解绑
    success = mysql_service.unbind_oauth_account(user_id, provider)

    if success:
        return api_response(
            success=True,
            message=f'{provider.capitalize()} account unbound successfully'
        )
    else:
        return error_response('Failed to unbind OAuth account', 500)


@user_bp.route('/oauth/accounts', methods=['GET'])
@jwt_required
@handle_errors
def get_bound_accounts():
    """获取当前用户绑定的 OAuth 账号列表"""
    user_id = g.current_user_id

    accounts = mysql_service.fetch_user_oauth_accounts(user_id)

    return api_response(
        success=True,
        message='Bound accounts fetched successfully',
        data={'accounts': accounts}
    )


# ==================== 删除用户 ====================
@user_bp.route('/<user_id>', methods=['DELETE'])
@handle_errors
def delete_user(user_id: str):
    """
    删除用户（级联删除相关数据）

    删除顺序：
    1. 删除用户关联的所有 assets（包括 OSS 中的图片和 MongoDB 中的 asset_data）
    2. 删除用户关联的所有 works（级联删除 chapters）
    3. 删除用户记录
    """
    # 验证必填字段（支持从 JSON 或查询参数传递 user_id）
    if not user_id:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        if not user_id:
            return error_response('User ID is required', 400)

    # 检查用户是否存在
    user = mysql_service.fetch_user_by_id(user_id)
    if not user:
        return error_response('User not found', 404)

    logger.info(f"Starting cascade delete for user: {user_id}")

    # 1. 获取用户的所有 assets
    user_assets = mysql_service.fetch_assets(user_id, limit=1000, offset=0)

    # 2. 删除每个 asset 及其关联的 OSS 图片和 MongoDB 数据
    deleted_assets_count = 0
    for asset in user_assets:
        asset_id = asset['asset_id']
        asset_type = asset['asset_type']
        asset_data = MongoService().fetch_asset_data(asset_id)

        # 如果是 comic 类型，删除 OSS 中的图片
        if asset_type == 'comic' and asset_data:
            oss_object_key = asset_data.get('oss_object_key')
            if oss_object_key:
                try:
                    picture_service.delete_picture(oss_object_key)
                    logger.info(f"Deleted OSS picture for asset: {asset_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete OSS picture {asset_id}: {e}")

        # 删除 MongoDB 中的 asset_data
        try:
            MongoService().delete_asset_data(asset_id)
            deleted_assets_count += 1
        except Exception as e:
            logger.error(f"Error deleting asset data {asset_id}: {e}")

    # 3. 从 MySQL 中删除 assets
    for asset in user_assets:
        try:
            mysql_service.delete_asset(asset['asset_id'])
        except Exception as e:
            logger.error(f"Error deleting asset {asset['asset_id']}: {e}")

    logger.info(f"Deleted {deleted_assets_count} assets for user: {user_id}")

    # 4. 获取用户的所有 works
    user_works = mysql_service.fetch_works_by_author_id(user_id, limit=1000, offset=0)

    # 5. 删除每个 work（级联删除 chapters）
    deleted_works_count = 0
    for work in user_works:
        work_id = work['work_id']

        # 获取作品的所有章节
        chapters = mysql_service.fetch_chapters_by_work_id(work_id, limit=1000, offset=0)

        # 删除章节
        for chapter in chapters:
            try:
                mysql_service.delete_chapter(chapter['chapter_id'])
            except Exception as e:
                logger.error(f"Error deleting chapter {chapter['chapter_id']}: {e}")

        # 删除 MongoDB 中的 work_details
        try:
            MongoService().delete_work_details(work_id)
        except Exception as e:
            logger.warning(f"Error deleting work details {work_id}: {e}")

        # 从 MySQL 中删除 work
        try:
            mysql_service.delete_work(work_id)
            deleted_works_count += 1
        except Exception as e:
            logger.error(f"Error deleting work {work_id}: {e}")

    logger.info(f"Deleted {deleted_works_count} works for user: {user_id}")

    # 6. 删除用户记录
    user_deleted = mysql_service.delete_user(user_id)

    if user_deleted:
        return api_response(
            success=True,
            message='User and all related data deleted successfully',
            data={
                'user_id': user_id,
                'deleted_assets': deleted_assets_count,
                'deleted_works': deleted_works_count
            },
            count=1
        )
    else:
        return error_response('Failed to delete user', 500)
