# api/routes/work.py
"""
作品路由模块
统一使用 MySQL/MongoDB 存储
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors
from utils.general_helper import validate_required_fields
from utils.resource_helper import (
    get_full_asset_by_id,
    get_full_work_by_id,
    build_work_data,
    parse_pagination_args,
    delete_work_cascade
)
from db import MySQLService, MongoService
import logging

work_bp = Blueprint('work', __name__)
logger = logging.getLogger(__name__)


@work_bp.route('/createWork', methods=['POST'])
@handle_errors
def create_work():
    """创建新的作品"""
    data = request.get_json()
    validate_required_fields(data, ['author_id', 'title'])

    work_data = build_work_data(data)

    try:
        work = MySQLService().insert_work(**work_data)
        work_id = work['work_id']
    except Exception as e:
        logger.error(f"Error creating work: {str(e)}")
        return error_response('Failed to create work', 500)

    try:
        MongoService().insert_work_details(work_id, asset_ids=[], chapter_ids=[])
    except Exception as e:
        logger.error(f"Error inserting work details: {str(e)}")
        return error_response('Failed to create work', 500)

    # 获取完整的作品信息
    full_work = get_full_work_by_id(work_id)

    return api_response(
        success=True,
        message='Work created successfully',
        data=full_work,
        count=1
    )


@work_bp.route('/updateWorkById', methods=['POST'])
@handle_errors
def update_work():
    """更新作品"""
    data = request.get_json()
    validate_required_fields(data, ['work_id'])

    work_id = data['work_id']
    update_fields = {}

    # 允许更新的字段列表
    allowed_fields = ['title', 'genre', 'tags', 'status', 'chapter_count', 'word_count', 'description', 'work_type']
    for field in allowed_fields:
        if field in data:
            update_fields[field] = data[field]

    if not update_fields:
        return error_response('No valid fields to update', 400)

    updated = MySQLService().update_work(work_id, update_fields)
    if not updated:
        return error_response('Failed to update work', 500)

    return api_response(
        success=True,
        message='Work updated successfully',
        data=updated,
        count=1
    )


@work_bp.route('/getWorkById', methods=['GET'])
@handle_errors
def get_work():
    """获取单个作品详情"""
    validate_required_fields(request.args, ['work_id'])
    work_id = request.args.get('work_id')

    work = get_full_work_by_id(work_id)
    if not work:
        return error_response('Work not found', 404)

    return api_response(
        success=True,
        message='Work fetched successfully',
        data=work,
        count=1
    )


@work_bp.route('/getWorksByAuthorId', methods=['GET'])
@handle_errors
def get_works_by_author_id():
    """根据作者 ID 获取作品列表"""
    validate_required_fields(request.args, ['author_id'])
    author_id = request.args.get('author_id')
    status = request.args.get('status', None)

    try:
        limit, offset = parse_pagination_args(request.args)
    except ValueError as e:
        return error_response(str(e), 400)

    works = MySQLService().fetch_works_by_author_id(author_id, status, limit, offset)
    return api_response(
        success=True,
        message='Works fetched successfully',
        data=works,
        count=len(works)
    )


@work_bp.route('/deleteWorkById', methods=['POST'])
@handle_errors
def delete_work():
    """删除作品"""
    data = request.get_json()
    validate_required_fields(data, ['work_id'])
    work_id = data['work_id']

    deleted = delete_work_cascade(work_id)

    if deleted:
        return api_response(
            success=True,
            message='Work deleted successfully',
            data=None,
            count=1
        )
    return error_response('Failed to delete work', 500)


# ---------- work_details 关联操作 ----------
@work_bp.route('/addAssetToWork', methods=['POST'])
@handle_errors
def add_asset_to_work():
    """将 asset 关联到作品"""
    data = request.get_json()
    validate_required_fields(data, ['work_id', 'asset_id'])

    work_id = data['work_id']
    asset_id = data['asset_id']

    # 验证 asset 是否存在
    asset = get_full_asset_by_id(asset_id)
    if not asset:
        return error_response('Asset not found', 404)

    try:
        updated = MongoService().add_asset_to_work(work_id, asset_id)
        if not updated:
            MongoService().insert_work_details(work_id, asset_ids=[asset_id], novel_ids=[], anime_ids=[])
    except Exception as e:
        logger.error(f"Error adding asset to work: {str(e)}")
        return error_response('Failed to add asset to work', 500)

    work_details = MongoService().fetch_work_details(work_id)
    return api_response(
        success=True,
        message='Asset added to work successfully',
        data={'work_id': work_id, 'asset_ids': work_details['asset_ids'] if work_details else []},
        count=1
    )


@work_bp.route('/getAssetsByWorkId', methods=['GET'])
@handle_errors
def get_assets_by_work_id():
    """根据 work_id 获取关联的资产列表"""
    validate_required_fields(request.args, ['work_id'])
    work_id = request.args.get('work_id')

    work_details = MongoService().fetch_work_details(work_id)
    if not work_details:
        return api_response(
            success=True,
            message='No assets found for this work',
            data={},
            count=0
        )

    asset_ids = work_details.get('asset_ids', [])
    if not asset_ids:
        return api_response(
            success=True,
            message='No assets found for this work',
            data={},
            count=0
        )

    assets = []
    for asset_id in asset_ids:
        asset_info = get_full_asset_by_id(asset_id)
        if asset_info:
            assets.append(asset_info)

    result = {'character': [], 'world': []}
    for asset in assets:
        asset_type = asset['asset_type']
        if asset_type in result:
            result[asset_type].append(asset)

    return api_response(
        success=True,
        message='Assets fetched successfully',
        data=result,
        count=len(assets)
    )


@work_bp.route('/removeAssetFromWork', methods=['POST'])
@handle_errors
def remove_asset_from_work():
    """从作品中移除资产"""
    data = request.get_json()
    validate_required_fields(data, ['work_id', 'asset_id'])

    work_id = data['work_id']
    asset_id = data['asset_id']

    try:
        removed = MongoService().remove_asset_from_work(work_id, asset_id)
        if not removed:
            return error_response('Failed to remove asset from work', 500)
    except Exception as e:
        logger.error(f"Error removing asset from work: {str(e)}")
        return error_response('Failed to remove asset from work', 500)

    work_details = MongoService().fetch_work_details(work_id)
    return api_response(
        success=True,
        message='Asset removed from work successfully',
        data={'work_id': work_id, 'asset_ids': work_details['asset_ids'] if work_details else []},
        count=1
    )
