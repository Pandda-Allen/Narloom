# api/routes/asset.py
"""
资产路由模块
统一使用 MySQL/MongoDB 存储
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors
from utils.general_helper import validate_required_fields
from utils.resource_helper import (
    get_full_asset_by_id,
    parse_pagination_args,
    delete_asset_cascade
)
from db import MySQLService, MongoService, work_service
import logging

asset_bp = Blueprint('asset', __name__)
logger = logging.getLogger(__name__)


@asset_bp.route('/createNewAsset', methods=['POST'])
@handle_errors
def create_asset():
    """创建新的资产（character 或 world）"""
    data = request.get_json()
    validate_required_fields(data, ['type', 'user_id'])

    user_id = data.get('user_id')
    asset_type = data.get('type')
    work_id = data.get('work_id')
    asset_data = data.get('asset_data', {})

    # 如果传入了 work_id，验证作品是否存在
    if work_id:
        work = work_service.fetch_work_by_id(work_id)
        if not work:
            return error_response('Work not found', 404)

    # 插入 MySQL 数据库
    mysql_row = MySQLService().insert_asset(user_id, asset_type, work_id)
    asset_id = mysql_row['asset_id']

    # 插入 MongoDB 数据库
    try:
        MongoService().insert_asset_data(asset_id, asset_data)
    except Exception as e:
        logger.error(f"Error inserting asset data to MongoDB: {str(e)}")
        # 回滚：删除 MySQL 中的数据
        MySQLService().delete_asset(asset_id)
        return error_response('Failed to create asset', 500)

    # 如果 work_id 有效，同步关联到 MongoDB 的 work_details
    if work_id:
        try:
            MongoService().add_asset_to_work(work_id, asset_id)
        except Exception as e:
            logger.error(f"Error adding asset to work: {str(e)}")
            # 这里不回滚，因为资产已经创建成功，只是关联失败不影响主体功能

    result = {
        'asset_id': mysql_row['asset_id'],
        'user_id': mysql_row['user_id'],
        'work_id': mysql_row['work_id'],
        'asset_type': mysql_row['asset_type'],
        'created_at': mysql_row['created_at'],
        'updated_at': mysql_row['updated_at'],
        'asset_data': asset_data
    }

    return api_response(
        success=True,
        message='Asset created successfully',
        data=result,
        count=1
    )


@asset_bp.route('/updateAssetById', methods=['POST'])
@handle_errors
def update_asset():
    """更新资产"""
    data = request.get_json()
    validate_required_fields(data, ['asset_id'])

    asset_id = data.get('asset_id')

    mysql_updates = {}
    mongo_updates = None

    if 'work_id' in data:
        mysql_updates['work_id'] = data['work_id']
    if 'type' in data:
        mysql_updates['asset_type'] = data['type']
    if 'asset_data' in data:
        mongo_updates = data['asset_data']

    # 检查资产是否存在
    existing_asset = MySQLService().fetch_asset_by_id(asset_id)
    if not existing_asset:
        return error_response('Asset not found', 404)

    # 更新 MySQL 数据库
    if mysql_updates:
        updated_asset = MySQLService().update_asset(asset_id, mysql_updates)
        if not updated_asset:
            return error_response('Asset not found for update', 404)

    # 更新 MongoDB 数据库
    if mongo_updates is not None:
        try:
            MongoService().update_asset_data(asset_id, mongo_updates)
        except Exception as e:
            logger.error(f"Error updating asset data in MongoDB: {str(e)}")
            return error_response('Failed to update asset data in MongoDB', 500)

    final_asset = MySQLService().fetch_asset_by_id(asset_id)
    final_asset_data = MongoService().fetch_asset_data(asset_id) or {}

    result = {
        'asset_id': final_asset['asset_id'],
        'user_id': final_asset['user_id'],
        'work_id': final_asset['work_id'],
        'asset_type': final_asset['asset_type'],
        'created_at': final_asset['created_at'],
        'updated_at': final_asset['updated_at'],
        'asset_data': final_asset_data
    }

    return api_response(
        success=True,
        message='Asset updated successfully',
        data=result,
        count=1
    )


@asset_bp.route('/getAssetById', methods=['GET'])
@handle_errors
def get_asset():
    """获取单个资产详情"""
    validate_required_fields(request.args, ['asset_id'])

    asset_id = request.args.get('asset_id')
    result = get_full_asset_by_id(asset_id)

    if not result:
        return error_response('Asset not found', 404)

    return api_response(
        success=True,
        message='Asset retrieved successfully',
        data=result,
        count=1
    )


@asset_bp.route('/getAssetsByUserId', methods=['GET'])
@handle_errors
def get_user_assets():
    """获取资产列表，支持按类型筛选"""
    validate_required_fields(request.args, ['user_id'])

    user_id = request.args.get('user_id')
    asset_type = request.args.get('type', None)
    work_id = request.args.get('work_id', None)

    try:
        limit, offset = parse_pagination_args(request.args)
    except ValueError as e:
        return error_response(str(e), 400)

    mysql_rows = MySQLService().fetch_assets(user_id, asset_type, work_id, limit, offset)
    if not mysql_rows:
        return api_response(
            success=True,
            message='No assets found',
            data=[],
            count=0
        )

    asset_ids = [row['asset_id'] for row in mysql_rows]
    asset_data_map = MongoService().fetch_multiple_asset_data(asset_ids)

    results = []
    for row in mysql_rows:
        results.append({
            'asset_id': row['asset_id'],
            'user_id': row['user_id'],
            'work_id': row['work_id'],
            'asset_type': row['asset_type'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'asset_data': asset_data_map.get(row['asset_id'], {})
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
    """删除资产"""
    data = request.get_json()
    validate_required_fields(data, ['asset_id'])
    asset_id = data.get('asset_id')

    deleted = delete_asset_cascade(asset_id)

    if deleted:
        return api_response(
            success=True,
            message='Asset deleted successfully',
            data=None,
            count=1
        )
    return error_response('Asset not found or delete failed', 404)
