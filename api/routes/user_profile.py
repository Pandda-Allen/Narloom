import supabase
from flask import Blueprint, jsonify, request, redirect, url_for
from utils.response_helper import error_response, api_response
from utils.general_helper import handle_errors

user_profile_bp = Blueprint('user_profile', __name__)

@user_profile_bp.route('/', methods=['POST'])
@handle_errors
def user_profile_update():
    data = request.get_json()
    user_id = data.get('id')

    response = (
        supabase.table('users')
        .update({
            "name": data.get('name'),
            "bio": data.get('bio'),
        })
        .eq('id', user_id)
        .execute()
    )

    if response and 'data' in response:
        return api_response(
            success=True,
            message='User Profile updated successfully',
            data={
                'id': response['data'][0].get('id', ''),
                'name': response['data'][0].get('name', ''),
                'bio': response['data'][0].get('bio', '')
            }
        )
    else:
        return error_response('User profile update failed', 400)
    