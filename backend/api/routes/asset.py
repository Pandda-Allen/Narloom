# api/routes/asset.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from services.supabase_service import SupabaseService
import json
from datetime import datetime

asset_bp = Blueprint('asset', __name__)

def read_asset_data(data, asset_type):
    """
    读取并解析前端回传的asset数据
    
    Args:
        data: 请求的JSON数据
        asset_type: asset类型 ('character' 或 'world')
    
    Returns:
        dict: 解析后的asset数据
    """
    try:
        if asset_type == 'character':
            asset_data = {
                'user_id': data.get('user_id', ''),
                'asset_id': data.get('id', None),
                'character_name': data.get('name', ''),
                'description': data.get('description', ''),
                'role': data.get('role', ''),
                'traits': json.dumps(data.get('traits', {})) if isinstance(data.get('traits'), dict) else data.get('traits', '{}'),
                'faction': data.get('faction', ''),
                'group': data.get('group', ''),
                'relationship': json.dumps(data.get('relationship', {})) if isinstance(data.get('relationship'), dict) else data.get('relationship', '{}'),
                'notes': data.get('notes', ''),
                'created_at': data.get('created_at', datetime.now().isoformat()),
                'updated_at': data.get('updated_at', datetime.now().isoformat())
            }
        elif asset_type == 'world':
            asset_data = {
                'user_id': data.get('user_id', ''),
                'world_name': data.get('name', ''),
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
                'created_at': data.get('created_at', datetime.now().isoformat()),
                'updated_at': data.get('updated_at', datetime.now().isoformat())
            }
        else:
            return None
            
        # 移除空值字段
        asset_data = {k: v for k, v in asset_data.items() if v is not None}
        return asset_data
        
    except Exception as e:
        raise ValueError(f"Error reading asset data: {str(e)}")

def format_supabase_response(response):
    """
    格式化Supabase响应，确保可以jsonify
    
    Args:
        response: Supabase响应对象
    
    Returns:
        dict: 格式化后的响应数据
    """
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
            
        # 如果数据是列表，处理每个元素
        if isinstance(data, list):
            formatted_data = []
            for item in data:
                if hasattr(item, '__dict__'):
                    formatted_item = {}
                    for key, value in item.__dict__.items():
                        if not key.startswith('_'):
                            # 处理特殊类型
                            if hasattr(value, 'isoformat'):
                                formatted_item[key] = value.isoformat()
                            else:
                                formatted_item[key] = value
                    formatted_data.append(formatted_item)
                elif isinstance(item, dict):
                    formatted_data.append(item)
                else:
                    formatted_data.append(str(item))
            return {'data': formatted_data, 'count': len(formatted_data)}
        
        # 如果数据是单个对象
        elif isinstance(data, dict):
            return {'data': [data], 'count': 1}
        
        # 其他情况
        else:
            return {'data': [str(data)], 'count': 1}
            
    except Exception as e:
        raise ValueError(f"Error formatting Supabase response: {str(e)}")

@asset_bp.route('/create', methods=['POST'])
def create_asset():
    """创建新的asset（character或world）"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided', 400)
        asset_type = data.get('type')  # 'character' 或 'world'
        
        if asset_type not in ['character', 'world']:
            return error_response('Invalid asset type. Must be "character" or "world"', 400)
        
        # 读取数据
        asset_data = read_asset_data(data, asset_type)
        if not asset_data:
            return error_response('Failed to read asset data', 400)
                
        # 插入到Supabase
        response = SupabaseService().asset_insert(asset_data, asset_type)
        
        # 格式化响应
        formatted_response = format_supabase_response(response)
        
        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message=f'{asset_type.capitalize()} asset created successfully',
                data=formatted_response.get('data')[0]
            )
        else:
            return error_response('Failed to create asset', 500)
            
    except ValueError as e:
        return error_response(f'Error processing request: {str(e)}', 400)
    except Exception as e:
        return error_response(f'Error creating asset: {str(e)}', 500)

@asset_bp.route('/update', methods=['POST'])
def update_asset():
    """更新asset"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided', 400)
        
        asset_type = data.get('type')  # 'character' 或 'world'
        asset_id = data.get('asset_id')
        
        if asset_type not in ['character', 'world']:
            return error_response('Invalid asset type. Must be "character" or "world"', 400)
        
        # 读取数据并添加更新时间
        asset_data = read_asset_data(data, asset_type)
        if not asset_data:
            return error_response('Failed to read asset data', 400)
        
        asset_data['updated_at'] = datetime.now().isoformat()
        
        # 更新Supabase
        response = SupabaseService().asset_update(asset_id, asset_data, asset_type)
        
        # 格式化响应
        formatted_response = format_supabase_response(response)
        
        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message=f'{asset_type.capitalize()} asset updated successfully',
                data=formatted_response.get('data')[0]
            )
        else:
            return error_response('Asset not found or update failed', 404)
            
    except ValueError as e:
        return error_response(f'Error processing request: {str(e)}', 400)
    except Exception as e:
        return error_response(f'Error updating asset: {str(e)}', 500)

@asset_bp.route('/get', methods=['GET'])
def get_asset():
    """获取单个asset详情"""
    try:
        # 获取asset类型（可选）
        asset_type = request.args.get('type')
        asset_id = request.args.get('asset_id')

        print(f"Fetching asset with ID: {asset_id} and type: {asset_type}")
        
        response = SupabaseService().asset_fetch_by_id(asset_id, asset_type)
        
        # 格式化响应
        formatted_response = format_supabase_response(response)
        
        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message='Asset retrieved successfully',
                data=formatted_response.get('data')[0]
            )
        else:
            return error_response('Asset not found', 404)
            
    except Exception as e:
        return error_response(f'Error retrieving asset: {str(e)}', 500)

@asset_bp.route('/getAll', methods=['GET'])
def get_all_assets():
    """获取asset列表，支持按类型筛选"""
    print("Received request to fetch all assets")
    try:
        asset_type = request.args.get('type', 'all')  # 可选：'character', 'world', 或不传获取全部
        user_id = request.args.get('user_id')  # 根据用户ID筛选资产
        limit = request.args.get('limit', 100)  # 默认限制100条
        offset = request.args.get('offset', 0)  # 分页偏移
        
        if user_id:
            response = SupabaseService().asset_fetch_all(asset_type, user_id, limit, offset)
        else:
            return error_response('User ID is required to fetch assets', 400)
        # 格式化响应
        formatted_response = format_supabase_response(response)
        
        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message='Assets retrieved successfully',
                data=formatted_response.get('data'),
                count=formatted_response.get('count')
            )
        else:
            return error_response('No assets found', 404)
            
    except Exception as e:
        return error_response(f'Error retrieving assets: {str(e)}', 500)

@asset_bp.route('/delete', methods=['POST'])
def delete_asset():
    """删除asset"""
    try:
        # 获取asset类型（可选）
        asset_type = request.args.get('type')
        asset_id = request.args.get('asset_id')
        
        if asset_type not in ['character', 'world']:
            return error_response('Invalid asset type. Must be "character" or "world"', 400)
        
        if not asset_id:
            return error_response('Asset ID is required for deletion', 400)
        
        response = SupabaseService().asset_delete(asset_id, asset_type)
        
        # 格式化响应
        formatted_response = format_supabase_response(response)
        
        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message='Asset deleted successfully',
                data={}
            )
        else:
            return error_response('Asset not found', 404)
            
    except Exception as e:
        return error_response(f'Error deleting asset: {str(e)}', 500)