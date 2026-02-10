import supabase
from flask import Blueprint, jsonify, request, redirect, url_for
from utils.response_helper import error_response, api_response
from services.supabase_service import SupabaseService

login_bp = Blueprint('login', __name__)

@login_bp.route('/', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    print("email:", email,
          " password:", password)

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
        print("Login error:", str(e))
        print(e)
        return error_response('Invalid credentials', 401)
    