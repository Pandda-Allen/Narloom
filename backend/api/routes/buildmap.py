# api/routes/buildmap.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response, format_supabase_response
from services.supabase_service import SupabaseService
import json
from datetime import datetime

buildmap_bp = Blueprint('buildmap', __name__)

def fetch_map_data(data):
    map_data = {
        'user_id': data.get('user_id', None),
        'work_id': data.get('work_id', None),
        'asset_id': data.get('asset_id', None),
        'notes': data.get('notes', ''),
        'created_at': data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'asset_type': data.get('asset_type', '')
    }

    # 移除空值字段
    map_data = {k: v for k, v in map_data.items() if v is not None}
    return map_data

@buildmap_bp.route('/buildMap', methods=['POST'])
def build_map():
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided', 400)

        map_data = fetch_map_data(data)
        if not map_data:
            return error_response('Invalid map data', 400)
        
        response = SupabaseService().map_insert(map_data)

        formatted_response = format_supabase_response(response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True, 
                message='Map created successfully', 
                data=formatted_response.get('data')[0]
            )
        else:
            return error_response('Failed to create map', 500)
        
    except ValueError as ve:
        return error_response(str(ve), 400)
    except Exception as e:
        return error_response(str(e), 500)
    
@buildmap_bp.route('/getMapByWorkId', methods=['GET'])
def get_map_by_work_id():
    try:
        data = request.get_json()
        print("Received data for getMapByWorkId:", data)  # 调试输出
        if not data:
            return error_response('No data provided', 400)
        
        user_id = data.get('user_id')
        work_id = data.get('work_id')
        if not user_id or not work_id:
            return error_response('user_id and work_id are required', 400)

        response = SupabaseService().map_fetch_by_ids(work_id, user_id)

        formatted_response = format_supabase_response(response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True, 
                message='Map fetched successfully', 
                data=formatted_response.get('data')[0]
            )
        else:
            return error_response('Failed to fetch map', 500)
        
    except Exception as e:
        return error_response(str(e), 500)

@buildmap_bp.route('/deleteMapById', methods=['POST'])
def delete_map_by_id():
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided', 400)
        
        user_id = data.get('user_id')
        asset_id = data.get('asset_id')
        work_id = data.get('work_id')
        if not user_id or not asset_id or not work_id:
            return error_response('user_id, asset_id and work_id are required', 400)

        response = SupabaseService().map_delete(asset_id, work_id, user_id)

        formatted_response = format_supabase_response(response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True, 
                message='Map deleted successfully', 
                data=formatted_response.get('data')[0]
            )
        else:
            return error_response('Failed to delete map', 500)
        
    except Exception as e:
        return error_response(str(e), 500)