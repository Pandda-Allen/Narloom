# api/routes/asset.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response, format_supabase_response
from utils.general_helper import get_request_json, handle_errors, validate_required_fields
from services.supabase_service import SupabaseService
import json
from datetime import datetime

asset_bp = Blueprint('asset', __name__)

def fetch_asset_data(data, asset_type):
    if asset_type == 'character':
        asset_data = {
            'user_id': data.get('user_id', ''),
            'asset_id': data.get('id', None),
            'character_name': data.get('name', ''),
            'description': data.get('description', ''),
            'role': data.get('role', ''),
            'traits': data.get('traits', '{}'),
            'faction': data.get('faction', ''),
            'group': data.get('group', ''),
            'relationship': data.get('relationship', '{}'),
            'notes': data.get('notes', ''),
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    elif asset_type == 'world':
        asset_data = {
            'user_id': data.get('user_id', ''),
            'asset_id': data.get('id', None),
            'world_name': data.get('name', ''),
            'description': data.get('description', ''),
            'location': json.dumps(data.get('location', {})) if isinstance(data.get('location'), dict) else data.get('location', '{}'),
            'rule': json.dumps(data.get('rule', {})) if isinstance(data.get('rule'), dict) else data.get('rule', '{}'),
            'system': json.dumps(data.get('system', {})) if isinstance(data.get('system'), dict) else data.get('system', '{}'),
            'item': json.dumps(data.get('item', [])) if isinstance(data.get('item'), list) else data.get('item', '[]'),
            'artifact': json.dumps(data.get('artifact', [])) if isinstance(data.get('artifact'), list) else data.get('artifact', '[]'),
            'nation': json.dumps(data.get('nation', [])) if isinstance(data.get('nation'), list) else data.get('nation', '[]'),
            'region': json.dumps(data.get('region', [])) if isinstance(data.get('region'), list) else data.get('region', '[]'),
            'event': json.dumps(data.get('event', [])) if isinstance(data.get('event'), list) else data.get('event', '[]'),
            'map': json.dumps(data.get('map', {})) if isinstance(data.get('map'), dict) else data.get('map', '{}'),
            'timeline': json.dumps(data.get('timeline', {})) if isinstance(data.get('timeline'), dict) else data.get('timeline', '{}'),
            'updated_at': datetime.now().isoformat()
        }
    else:
        return None
        
    return {k: v for k, v in asset_data.items() if v is not None}

@asset_bp.route('/createNewAsset', methods=['POST'])
@handle_errors
def create_asset():
    """创建新的asset（character或world）"""
    data = get_request_json()
    validate_required_fields(data, ['type', 'user_id'])  # type: character/world

    asset_type = data.get('type')
    if asset_type not in ['character', 'world']:
        return error_response('Invalid asset type. Must be "character" or "world"', 400)
    
    asset_data = fetch_asset_data(data, asset_type)
    asset_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
    response = SupabaseService().asset_insert(asset_data, asset_type)
    formatted = format_supabase_response(response)
    
    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True,
            message=f'{asset_type.capitalize()} asset created successfully',
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Failed to create asset', 500)

@asset_bp.route('/updateAssetById', methods=['POST'])
@handle_errors
def update_asset():
    """更新asset"""
    data = get_request_json()
    validate_required_fields(data, ['type', 'asset_id'])
    
    asset_type = data.get('type')  # 'character' 或 'world'
    asset_id = data.get('asset_id')
    
    if asset_type not in ['character', 'world']:
        return error_response('Invalid asset type. Must be "character" or "world"', 400)
    
    asset_data = fetch_asset_data(data, asset_type)
    asset_data['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    response = SupabaseService().asset_update(asset_id, asset_data, asset_type)
    formatted = format_supabase_response(response)
    
    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True,
            message=f'{asset_type.capitalize()} asset updated successfully',
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Asset not found or update failed', 404)

@asset_bp.route('/getAssetById', methods=['GET'])
@handle_errors
def get_asset():
    """获取单个asset详情"""
    validate_required_fields(request.args, ['asset_id', 'type'])

    asset_id = request.args.get('asset_id')
    asset_type = request.args.get('type')
    
    response = SupabaseService().asset_fetch_by_id(asset_id, asset_type)
    formatted = format_supabase_response(response)
    
    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True,
            message='Asset retrieved successfully',
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Asset not found', 404)

@asset_bp.route('/getAssetsByUserId', methods=['GET'])
@handle_errors
def get_user_assets():
    """获取asset列表，支持按类型筛选"""
    validate_required_fields(request.args, ['user_id'])
    
    response = SupabaseService().asset_fetch_all(
        request.args.get('type', 'all'),    # 可选：'character', 'world', 或不传获取全部
        request.args.get('user_id'),        # 根据用户ID筛选资产
        request.args.get('limit', 100),     # 默认限制100条
        request.args.get('offset', 0)       # 分页偏移
    )
    formatted = format_supabase_response(response)
    
    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True,
            message='Assets retrieved successfully',
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('No assets found', 404)

@asset_bp.route('/deleteAssetById', methods=['POST'])
@handle_errors
def delete_asset():
    """删除asset"""
    validate_required_fields(request.args, ['asset_id', 'type'])

    asset_type = request.args.get('type')
    asset_id = request.args.get('asset_id')
    
    if asset_type not in ['character', 'world']:
        return error_response('Invalid asset type. Must be "character" or "world"', 400)
    
    response = SupabaseService().asset_delete(asset_id, asset_type)
    formatted = format_supabase_response(response)
    
    if formatted and formatted.get('count') == 0:
        return api_response(
            success=True,
            message='Asset deleted successfully',
            data=formatted.get('data') if formatted.get('data') else None,
            count=formatted.get('count')
        )
    return error_response('Asset delete failed', 404)
