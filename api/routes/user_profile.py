from flask import Blueprint, jsonify, request, redirect, url_for
from utils.response_helper import error_response, api_response
from utils.general_helper import handle_errors
from services.mysql_service import mysql_service

user_profile_bp = Blueprint('user_profile', __name__)

@user_profile_bp.route('/', methods=['POST'])
@handle_errors
def user_profile_update():
    data = request.get_json()
    user_id = data.get('id')

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
                'id': updated_user.get('user_id', ''),
                'name': updated_user.get('name', ''),
                'bio': updated_user.get('bio', '')
            }
        )
    else:
        # 用户不存在，可能尚未在MySQL中创建，尝试插入
        try:
            new_user = mysql_service.insert_user(
                user_id=user_id,
                name=data.get('name', ''),
                bio=data.get('bio', '')
            )
            return api_response(
                success=True,
                message='User Profile created successfully',
                data={
                    'id': new_user.get('user_id', ''),
                    'name': new_user.get('name', ''),
                    'bio': new_user.get('bio', '')
                }
            )
        except Exception as e:
            return error_response('User profile update failed: user does not exist and cannot be created', 400)
    