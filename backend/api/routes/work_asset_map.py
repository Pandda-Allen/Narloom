# api/routes/work_asset_map.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response, format_supabase_response
from services.supabase_service import SupabaseService
import json
from datetime import datetime
from utils.general_helper import handle_errors, get_request_json, validate_required_fields

work_asset_map_bp = Blueprint('work_asset_map', __name__)

def fetch_map_data(data):
    map_data = {
        'user_id': data.get('user_id', None),
        'work_id': data.get('work_id', None),
        'asset_id': data.get('asset_id', None),
        'notes': data.get('notes', ''),
        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'asset_type': data.get('asset_type', '')
    }
    return {k: v for k, v in map_data.items() if v is not None}

def parse_map_data_asset(map_response):
    try:
        if not map_response:
            return {'character': [], 'world': []}
        
        # 处理不同的响应结构
        if hasattr(map_response, 'data'):
            data = map_response.data
        elif isinstance(map_response, dict) and 'data' in map_response:
            data = map_response['data']
        else:
            data = map_response

        result = {'character': [], 'world': []}

        for item in data:
            asset_id  = item.get('asset_id')
            asset_type = item.get('asset_type')

            if asset_type not in ['character', 'world']:
                continue

            asset_resp = SupabaseService().asset_fetch_by_id(asset_id , asset_type)
            if asset_resp and asset_resp.data:
                result[asset_type].append(asset_resp.data[0])
        return result
    
    except Exception as e:
        raise ValueError(f"Error parsing map data asset: {str(e)}")        

@work_asset_map_bp.route('/createNewMap', methods=['POST'])
@handle_errors
def create_new_map():
    data = get_request_json()
    validate_required_fields(data, ['user_id', 'work_id', 'asset_id', 'asset_type'])

    map_data = fetch_map_data(data)
    map_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    response = SupabaseService().map_insert(map_data)
    formatted = format_supabase_response(response)

    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True, 
            message='Map created successfully', 
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Failed to create map', 500)

@work_asset_map_bp.route('/getAssetsByWorkId', methods=['GET'])
@handle_errors
def get_assets_by_work_id():
    data = get_request_json()
    validate_required_fields(data, ['user_id', 'work_id'])

    response = SupabaseService().map_fetch_by_ids(data['work_id'], data['user_id'])
    parsed = parse_map_data_asset(response)

    return api_response(
        success=True, 
        message='Map fetched successfully', 
        data=parsed,
        count=len(parsed['character']) + len(parsed['world'])
    )


@work_asset_map_bp.route('/deleteMapById', methods=['POST'])
@handle_errors
def delete_map_by_id():
    data = get_request_json()
    validate_required_fields(data, ['user_id', 'asset_id', 'work_id'])

    response = SupabaseService().map_delete(
        data['asset_id'], 
        data['work_id'], 
        data['user_id']
    )
    formatted = format_supabase_response(response)

    if formatted and formatted.get('count') == 0:
        return api_response(
            success=True, 
            message='Map deleted successfully', 
            data=formatted.get('data') if formatted.get('data') else None,
            count=formatted.get('count')
        )
    return error_response('Failed to delete map', 500)