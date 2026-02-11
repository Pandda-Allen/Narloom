# api/routes/work_asset_map.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response, format_supabase_response
from services.supabase_service import SupabaseService
import json
from datetime import datetime

work_asset_map_bp = Blueprint('work_asset_map', __name__)

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

@work_asset_map_bp.route('/createNewMap', methods=['POST'])
def create_new_map():
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
    
def parse_map_data_asset(map_response):
    try:
        if not map_response:
            return None
        
        # 处理不同的响应结构
        if hasattr(map_response, 'data'):
            data = map_response.data
        elif isinstance(map_response, dict) and 'data' in map_response:
            data = map_response['data']
        else:
            data = map_response

        result_data = {
            'character': [],
            'world': []
        }

        for item in data:
            item_id = item.get('asset_id')
            item_type = item.get('asset_type')

            if item_type == 'character':
                asset_response = SupabaseService().asset_fetch_by_id(item_id, 'character')
            elif item_type == 'world':
                asset_response = SupabaseService().asset_fetch_by_id(item_id, 'world')
            else:
                continue

            if asset_response.data:
                result_data[item_type].append(asset_response.data[0])
        return result_data
    
    except KeyError as ke:
        raise ValueError(f"Error parsing map data asset: Missing key {str(ke)}")
    except Exception as e:
        raise ValueError(f"Error parsing map data asset: {str(e)}")        

@work_asset_map_bp.route('/getAssetsByWorkId', methods=['GET'])
def get_assets_by_work_id():
    try:
        data = request.get_json()

        if not data:
            return error_response('No data provided', 400)
        
        user_id = data.get('user_id')
        work_id = data.get('work_id')
        if not user_id or not work_id:
            return error_response('user_id and work_id are required', 400)

        response = SupabaseService().map_fetch_by_ids(work_id, user_id)

        parse_response = parse_map_data_asset(response)

        formatted_response = format_supabase_response(parse_response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True, 
                message='Map fetched successfully', 
                data=formatted_response.get('data'),
                count=formatted_response.get('count')
            )
        else:
            return error_response('Failed to fetch map', 500)
        
    except Exception as e:
        return error_response(str(e), 500)

@work_asset_map_bp.route('/deleteMapById', methods=['POST'])
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