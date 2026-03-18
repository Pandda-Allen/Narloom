"""
用户路由模块
整合登录、注册和用户资料管理功能
"""
from flask import Blueprint, request
from utils.response_helper import api_response, error_response
from utils.decorators import handle_errors
from services.mysql_service import mysql_service

# ==================== 蓝图定义 ====================
login_bp = Blueprint('login', __name__)
user_profile_bp = Blueprint('user_profile', __name__)
register_bp = Blueprint('register', __name__)

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
        'created_at': user.get('created_at')
    }


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

    return api_response(
        success=True,
        message='Registration successful',
        data=build_user_response(user)
    )


# ==================== 用户登录 ====================
@login_bp.route('/', methods=['POST'])
@handle_errors
def login():
    """用户登录"""
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
            return api_response(
                success=True,
                message='Login successful',
                data=build_user_response(user)
            )
        else:
            return error_response('Invalid credentials', 401)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Login error for email {email}: {type(e).__name__}")
        return error_response('Invalid credentials', 401)


# ==================== 用户资料管理 ====================
@user_profile_bp.route('/', methods=['POST'])
@handle_errors
def update_user_profile():
    """更新用户资料"""
    data = request.get_json()
    user_id = data.get('user_id')

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
        return error_response('User not found', 404)
