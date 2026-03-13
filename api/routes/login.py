import supabase
from flask import Blueprint, jsonify, request, redirect, url_for
from utils.response_helper import error_response, api_response
from utils.general_helper import handle_errors
from services.supabase_service import SupabaseService

login_bp = Blueprint('login', __name__)

@login_bp.route('/', methods=['POST'])
@handle_errors
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        response = supabase.auth.sign_in_with_password(
            {
                'email': email,
                'password': password
            }
        )

        if response and 'user' in response:
            return api_response(
                success=True,
                message='Login successful',
                data={
                    'user': response['user'],
                    'session': response.get('session'),
                }
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
    