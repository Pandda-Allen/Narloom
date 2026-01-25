from flask import jsonify
from datetime import datetime

def api_response(success=True, message="", data=None, status_code=200):
    response = {
        'status': 'success' if success else 'error',
        'message': message,
        'data': data or {},
    }
    return jsonify(response), status_code
def error_response(message="An error occurred", status_code=400, details=None):
    response = {
        'status': 'error', 
        'message': message,
        'details': details,
    }
    return jsonify(response), status_code