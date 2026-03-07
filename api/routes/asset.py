# api/routes/asset.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response, format_supabase_response
from utils.general_helper import get_request_json, handle_errors, validate_required_fields
from services.supabase_service import SupabaseService
from services.mysql_service import MySQLService
import json
from datetime import datetime

asset_bp = Blueprint('asset', __name__)

def fetch_asset_data(data):
    if data.get('type') not in ['character', 'world']:
        raise ValueError('Invalid asset type')
    proc_data = {
        'user_id': data.get('user_id', ''),
        'asset_id': data.get('id', None),
        'asset_type': data.get('type', ''),
        'work_id': data.get('work_id', None),
        'asset_data': data.get('asset_data', None)
    }        
    return {k: v for k, v in proc_data.items() if v is not None}

@asset_bp.route('/createNewAsset', methods=['POST'])
@handle_errors
def create_asset():
    """创建新的asset（character或world）"""
    data = get_request_json()
    validate_required_fields(data, ['type', 'user_id'])  # type: character/world

    asset_data = fetch_asset_data(data)

    mysql_row = MySQLService().insert_asset(
        asset_data.get('user_id'),
        asset_data.get('asset_type'),
        asset_data.get('work_id')
    )

    asset_id = mysql_row['asset_id']

    result = {
        'asset_id': mysql_row['asset_id'],
        'user_id': mysql_row['user_id'],
        'work_id': mysql_row['work_id'],
        'asset_type': mysql_row['asset_type'],
        'created_at': mysql_row['created_at'],
        'updated_at': mysql_row['updated_at']
    }

    if asset_id:
        return api_response(
            success=True,
            message='asset created successfully',
            data=result,
            count=1
        )
    return error_response('Failed to create asset', 500)

@asset_bp.route('/updateAssetById', methods=['POST'])
@handle_errors
def update_asset():
    """更新asset"""
    data = get_request_json()
    validate_required_fields(data, ['asset_id'])
    
    asset_id = data.get('asset_id')
    
    mysql_updates = {}

    if 'work_id' in data:
        mysql_updates['work_id'] = data['work_id']
    if 'type' in data:
        mysql_updates['asset_type'] = data['type']

    if mysql_updates:
        updated_asset = MySQLService().update_asset(asset_id, mysql_updates)
        if not updated_asset:
            return error_response('Asset not found for update', 404)
    else:
        exiting_asset = MySQLService().fetch_asset_by_id(asset_id)
        if not exiting_asset:
            return error_response('Asset not found for update', 404)
    
    final_asset = MySQLService().fetch_asset_by_id(asset_id)

    result = {
        'asset_id': final_asset['asset_id'],
        'user_id': final_asset['user_id'],
        'work_id': final_asset['work_id'],
        'asset_type': final_asset['asset_type'],
        'created_at': final_asset['created_at'],
        'updated_at': final_asset['updated_at']
    }
    
    return api_response(
        success=True,
        message='asset updated successfully',
        data=result,
        count=1
    )

@asset_bp.route('/getAssetById', methods=['GET'])
@handle_errors
def get_asset():
    """获取单个asset详情"""
    validate_required_fields(request.args, ['asset_id'])

    asset_id = request.args.get('asset_id')
    mysql_row = MySQLService().fetch_asset_by_id(asset_id)
    if not mysql_row:
        return error_response('Asset not found', 404)

    result = {
        'asset_id': mysql_row['asset_id'],
        'user_id': mysql_row['user_id'],
        'work_id': mysql_row['work_id'],
        'asset_type': mysql_row['asset_type'],
        'created_at': mysql_row['created_at'],
        'updated_at': mysql_row['updated_at']
    }
    
    return api_response(
        success=True,
        message='Asset retrieved successfully',
        data=result,
        count=1
    )

@asset_bp.route('/getAssetsByUserId', methods=['GET'])
@handle_errors
def get_user_assets():
    """获取asset列表，支持按类型筛选"""
    validate_required_fields(request.args, ['user_id'])
    
    user_id = request.args.get('user_id')
    asset_type = request.args.get('type', None)
    work_id = request.args.get('work_id', None)
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    mysql_rows = MySQLService().fetch_assets(user_id, asset_type, work_id, limit, offset)
    if not mysql_rows:
        return api_response(
            success=True,
            message='No assets found',
            data=[],
            count=0
        )

    results = []
    for row in mysql_rows:
        results.append({
            'asset_id': row['asset_id'],
            'user_id': row['user_id'],
            'work_id': row['work_id'],
            'asset_type': row['asset_type'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        })

    return api_response(
        success=True,
        message='Assets retrieved successfully',
        data=results,
        count=len(results)
    )

@asset_bp.route('/deleteAssetById', methods=['POST'])
@handle_errors
def delete_asset():
    """删除asset"""
    data = get_request_json()
    validate_required_fields(data, ['asset_id'])
    asset_id = data.get('asset_id')

    deleted = MySQLService().delete_asset(asset_id)

    if deleted:
        return api_response(
            success=True,
            message='Asset deleted successfully',
            data=None,
            count=1
        )
    return error_response('Asset not found or delete failed', 404)