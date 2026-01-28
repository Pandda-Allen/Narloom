import supabase
import os
import app
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
        response = SupabaseService().client_login(email, password)

        if response and response.user: # currently response cannot be jsonify, need to fix
            return api_response(
                success=True,
                message='Login successful',
                data = response.user
            )
        else:
            print("Invalid credentials")
            return error_response('Invalid credentials', 401)

    except Exception as e:
        print("Login error:", str(e))
        return error_response('Invalid credentials', 401)
    