import supabase
from flask import Blueprint, jsonify, request, redirect, url_for
from utils.response_helper import error_response, api_response

login_bp = Blueprint('login', __name__)

@login_bp.route('/', methods=['POST'])
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
        return error_response('Invalid credentials', 401)
    