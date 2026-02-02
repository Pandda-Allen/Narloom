# api/routes/asset.py
import supabase
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from services.supabase_service import SupabaseService

asset_bp = Blueprint('asset', __name__)

@asset_bp.route('/', methods=['POST'])
def create_asset():
    """创建新的asset（character或world）"""
    data = request.get_json()
    asset_type = data.get('type')  # 'character' 或 'world'
    
    if asset_type not in ['character', 'world']:
        return error_response('Invalid asset type. Must be "character" or "world"', 400)
    
    try:
        # 根据类型添加特定字段
        if asset_type == 'character':
            asset_data = {
                'user_id': data.get('user_id', ''),
                'character_name': data.get('name', ''),
                'description': data.get('description', ''),
                'role': data.get('role', ''),
                'traits': data.get('traits', {}),
                'faction': data.get('faction', ''),
                'group': data.get('group', ''),
                'relationship': data.get('relationship', {}),
                'notes': data.get('notes', ''),
                'created_at': data.get('created_at', 'now()'),
                'updated_at': data.get('updated_at', 'now()')
            }
            
        elif asset_type == 'world':
            world_data = {
                'user_id': data.get('user_id', ''),
                'world_name': data.get('name', ''),
                'location': data.get('location', {}),
                'rule': data.get('rule', {}),
                'system': data.get('system', {}),
                'item': data.get('item', []),
                'artifact': data.get('artifact', []),
                'nation': data.get('nation', []),
                'region': data.get('region', []),
                'event': data.get('event', []),
                'map': data.get('map', {}),
                'timeline': data.get('timeline', {})
            }
        
        # 插入到Supabase
        response = SupabaseService().asset_insert(asset_data, asset_type)

        if response and 'data' in response and len(response['data']) > 0: # currently response cannot be jsonify, need to fix
            return api_response(
                success=True,
                message=f'{asset_type.capitalize()} asset created successfully',
                data=response['data'][0]
            )
        else:
            return error_response('Failed to create asset', 500)
            
    except Exception as e:
        return error_response(f'Error creating asset: {str(e)}', 500)

@asset_bp.route('/', methods=['GET'])
def get_assets():
    """获取asset列表，支持按类型筛选"""
    asset_type = request.args.get('type')  # 可选：'character', 'world', 或不传获取全部
    user_id = request.args.get('user_id')  # 根据用户ID筛选资产
    
    try:
        response = SupabaseService().asset_fetch(asset_type, user_id)
                  
        if response and 'data' in response:
            return api_response(  # currently response cannot be jsonify, need to fix
                success=True,
                message='Assets retrieved successfully',
                data=response['data']
            )
        else:
            return error_response('No assets found', 404)
            
    except Exception as e:
        return error_response(f'Error retrieving assets: {str(e)}', 500)

# @asset_bp.route('/<asset_id>', methods=['GET'])
# def get_asset(asset_id):
#     """获取单个asset详情"""
#     try:
#         response = supabase.table('assets').select('*').eq('id', asset_id).execute()
        
#         if response and 'data' in response and len(response['data']) > 0:
#             return api_response(
#                 success=True,
#                 message='Asset retrieved successfully',
#                 data=response['data'][0]
#             )
#         else:
#             return error_response('Asset not found', 404)
            
#     except Exception as e:
#         return error_response(f'Error retrieving asset: {str(e)}', 500)

# @asset_bp.route('/<asset_id>', methods=['PUT'])
# def update_asset(asset_id):
#     """更新asset"""
#     data = request.get_json()
    
#     try:
#         # 更新基础字段
#         update_data = {
#             'name': data.get('name'),
#             'description': data.get('description'),
#             'updated_at': 'now()'
#         }
        
#         # 根据类型更新特定数据
#         asset_type = data.get('type')
#         if asset_type == 'character':
#             update_data['character_data'] = {
#                 'role': data.get('role'),
#                 'traits': data.get('traits'),
#                 'faction': data.get('faction'),
#                 'group': data.get('group'),
#                 'relationship': data.get('relationship'),
#                 'notes': data.get('notes')
#             }
#         elif asset_type == 'world':
#             update_data['world_data'] = {
#                 'location': data.get('location'),
#                 'rule': data.get('rule'),
#                 'system': data.get('system'),
#                 'item': data.get('item'),
#                 'artifact': data.get('artifact'),
#                 'nation': data.get('nation'),
#                 'region': data.get('region'),
#                 'event': data.get('event'),
#                 'map': data.get('map'),
#                 'timeline': data.get('timeline')
#             }
        
#         response = supabase.table('assets').update(update_data).eq('id', asset_id).execute()
        
#         if response and 'data' in response:
#             return api_response(
#                 success=True,
#                 message='Asset updated successfully',
#                 data=response['data'][0]
#             )
#         else:
#             return error_response('Asset not found', 404)
            
#     except Exception as e:
#         return error_response(f'Error updating asset: {str(e)}', 500)

# @asset_bp.route('/<asset_id>', methods=['DELETE'])
# def delete_asset(asset_id):
    # """删除asset"""
    # try:
    #     response = supabase.table('assets').delete().eq('id', asset_id).execute()
        
    #     if response and 'data' in response:
    #         return api_response(
    #             success=True,
    #             message='Asset deleted successfully',
    #             data={}
    #         )
    #     else:
    #         return error_response('Asset not found', 404)
            
    # except Exception as e:
    #     return error_response(f'Error deleting asset: {str(e)}', 500)