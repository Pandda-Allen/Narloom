from flask import jsonify
from datetime import datetime

def api_response(success=True, message="", data=None, status_code=200, count=1):
    response = {
        'status': 'success' if success else 'error',
        'message': message,
        'data': data or {},
        'count': count
    }
    return jsonify(response), status_code
def error_response(message="An error occurred", status_code=400, details=None):
    response = {
        'status': 'error', 
        'message': message,
        'details': details,
    }
    return jsonify(response), status_code

def format_supabase_response(response):
    try:
        if not response:
            return None
            
        # 处理不同的响应结构
        if hasattr(response, 'data'):
            data = response.data
        elif isinstance(response, dict) and 'data' in response:
            data = response['data']
        else:
            data = response

        return {'data': data, 'count': len(data) if isinstance(data, list) else 1}    
    except Exception as e:
        raise ValueError(f"Error formatting Supabase response: {str(e)}")