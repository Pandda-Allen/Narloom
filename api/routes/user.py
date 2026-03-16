"""
用户相关路由
整合登录、注册和用户资料管理功能
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.general_helper import handle_errors
from services.mysql_service import mysql_service

# ==================== 蓝图定义 ====================
login_bp = Blueprint('login', __name__)
user_profile_bp = Blueprint('user_profile', __name__)
register_bp = Blueprint('register', __name__)

# ==================== 用户注册 ====================
@register_bp.route('/', methods=['POST'])
@handle_errors
def register():
    """用户注册"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')
    bio = data.get('bio', '')

    if not email or not password:
        return error_response('Email and password are required', 400)

    # 验证邮箱格式
    if '@' not in email:
        return error_response('Invalid email format', 400)

    # 验证密码长度
    if len(password) < 6:
        return error_response('Password must be at least 6 characters', 400)

    # 注册用户
    user = mysql_service.register_user(email, password, name, bio)

    if user is None:
        return error_response('Email already registered', 409)

    # 返回注册成功的用户信息（不包含密码哈希）
    user_response = {
        'user_id': user.get('user_id'),
        'email': user.get('email'),
        'name': user.get('name', ''),
        'bio': user.get('bio', ''),
        'created_at': user.get('created_at')
    }

    return api_response(
        success=True,
        message='Registration successful',
        data=user_response
    )

# ==================== 用户登录 ====================
@login_bp.route('/', methods=['POST'])
@handle_errors
def login():
    """用户登录（使用MySQL认证）"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return error_response('Email and password are required', 400)

    try:
        # 使用MySQL进行认证
        user = mysql_service.authenticate_user(email, password)

        if user:
            # 确保用户在数据库中有完整记录（如果是从旧系统迁移的用户）
            _ensure_user_in_mysql(user.get('user_id'), email, user.get('name', ''), user.get('bio', ''))

            # 返回登录成功的用户信息（不包含密码哈希）
            user_response = {
                'user_id': user.get('user_id'),
                'email': user.get('email'),
                'name': user.get('name', ''),
                'bio': user.get('bio', ''),
                'created_at': user.get('created_at')
            }

            return api_response(
                success=True,
                message='Login successful',
                data=user_response
            )
        else:
            return error_response('Invalid credentials', 401)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        # 记录错误但不暴露敏感信息
        logger.error(f"Login error for email {email}: {type(e).__name__}")
        # 返回通用认证错误，不透露具体失败原因
        return error_response('Invalid credentials', 401)

# ==================== 用户资料管理（使用 MySQL 存储）====================
@user_profile_bp.route('/', methods=['POST'])
@handle_errors
def user_profile_update():
    """更新用户资料"""
    data = request.get_json()
    user_id = data.get('user_id')  # 注意：从id改为user_id以保持一致性

    if not user_id:
        return error_response('User ID is required', 400)

    # 构建更新数据
    update_data = {}
    if 'name' in data:
        update_data['name'] = data.get('name')
    if 'bio' in data:
        update_data['bio'] = data.get('bio')

    if not update_data:
        return error_response('No fields to update', 400)

    # 更新用户资料
    updated_user = mysql_service.update_user(user_id, update_data)

    if updated_user:
        return api_response(
            success=True,
            message='User Profile updated successfully',
            data={
                'user_id': updated_user.get('user_id', ''),
                'name': updated_user.get('name', ''),
                'bio': updated_user.get('bio', '')
            }
        )
    else:
        # 用户不存在，尝试插入（这种情况应该很少见，因为用户应该先登录或注册）
        try:
            # 这里需要email，但如果没有提供，使用默认值
            email = data.get('email', f"user_{user_id}@example.com")
            new_user = mysql_service.insert_user(
                user_id=user_id,
                email=email,
                name=data.get('name', ''),
                bio=data.get('bio', '')
            )
            return api_response(
                success=True,
                message='User Profile created successfully',
                data={
                    'user_id': new_user.get('user_id', ''),
                    'name': new_user.get('name', ''),
                    'bio': new_user.get('bio', '')
                }
            )
        except Exception as e:
            return error_response('User profile update failed: user does not exist and cannot be created', 400)

# ==================== 辅助函数 ====================
def _ensure_user_in_mysql(user_id: str, email: str, name: str = '', bio: str = ''):
    """确保用户在 MySQL 数据库中有完整记录"""
    if not user_id:
        return

    # 检查用户是否已存在
    existing_user = mysql_service.fetch_user_by_id(user_id)
    if existing_user:
        # 如果用户存在但缺少email，尝试更新
        if not existing_user.get('email') and email:
            try:
                mysql_service.update_user(user_id, {'email': email})
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to update email for user {user_id}: {e}")
        return

    # 插入新用户记录
    try:
        mysql_service.insert_user(
            user_id=user_id,
            email=email,
            name=name,
            bio=bio
        )
    except Exception as e:
        # 记录错误但不要影响登录流程
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to create user {user_id} in MySQL: {e}")