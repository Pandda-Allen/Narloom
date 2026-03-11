# api/routes/work.py
from flask import Blueprint, request
from api.routes import asset
from utils.response_helper import error_response, api_response, format_supabase_response
from utils.general_helper import handle_errors, get_request_json, validate_required_fields
from services.supabase_service import SupabaseService
from services.mysql_service import MySQLService
from services.mongo_service import MongoService
import json, logging
from datetime import datetime

work_bp = Blueprint('work', __name__)
logger = logging.getLogger(__name__)

def get_asset_by_id(asset_id):
    """从 MySQL 和 MongoDB 获取完整的资产信息"""
    mysql_row = MySQLService.fetch_asset_by_id(asset_id)
    if not mysql_row:
        return None
    asset_data = MongoService.fetch_asset_data_by_asset_id(asset_id)
    return {
        'asset_id': mysql_row['asset_id'],
        'user_id': mysql_row['user_id'],
        'work_id': mysql_row['work_id'],
        'asset_type': mysql_row['asset_type'],
        'created_at': mysql_row['created_at'],
        'updated_at': mysql_row['updated_at'],
        'asset_data': asset_data
    }

def fetch_novel_data(data):
    novel_data = {
        'author_id': data.get('author_id'),
        'novel_id': data.get('novel_id', None),
        'title': data.get('title'),
        'genre': data.get('genre', ''),
        'tags': data.get('tags', []),
        'status': data.get('status', 'draft'),
        'chapter_count': data.get('chapter_count', 0),
        'word_count': data.get('word_count', 0),
        'description': data.get('description', ''),
    }
    return {k: v for k, v in novel_data.items() if v is not None}

@work_bp.route('/createNovel', methods=['POST'])
@handle_errors
def create_novel():
    """创建新的work(novel)"""
    data = get_request_json()
    validate_required_fields(data, ['author_id', 'title'])

    novel_data = fetch_novel_data(data)

    try:
        work = MySQLService.insert_work(**novel_data)
        work_id = work['work_id']
    except Exception as e:
        logger.error(f"Error creating novel: {str(e)}")
        return error_response('Failed to create novel', 500)
    
    try:
        MongoService.insert_work_details(work_id, asset_ids=[], chapter_ids=[])
    except Exception as e:
        logger.error(f"Error inserting work details: {str(e)}")
        return error_response('Failed to create novel', 500)

@work_bp.route('/updateNovelById', methods=['POST'])
@handle_errors
def update_novel():
    """更新work(novel)"""
    data = get_request_json()
    validate_required_fields(data, ['work_id'])

    work_id = data['work_id']
    update_fields = {}

    if 'title' in data:
        update_fields['title'] = data['title']
    if 'genre' in data:
        update_fields['genre'] = data['genre']
    if 'tags' in data:
        update_fields['tags'] = data['tags']
    if 'status' in data:
        update_fields['status'] = data['status']
    if 'chapter_count' in data:
        update_fields['chapter_count'] = data['chapter_count']
    if 'word_count' in data:
        update_fields['word_count'] = data['word_count']
    if 'description' in data:
        update_fields['description'] = data['description']

    if not update_fields:
        return error_response('No valid fields to update', 400)
    
    updated = MySQLService.update_work(
        work_id,
        update_fields
    )
    if not updated:
        return error_response('Failed to update novel', 500)
    return api_response(
        success=True,
        message='Work updated successfully',
        data=updated,
        count=1
    )

@work_bp.route('/getNovelById', methods=['GET'])
@handle_errors
def get_novel():
    """获取单个work(novel)详情"""
    validate_required_fields(request.args, ['novel_id'])
    work_id = request.args.get('novel_id')
    work = MySQLService.fetch_work_by_id(work_id)
    if not work:
        return error_response('Novel not found', 404)
    return api_response(
        success=True,
        message='Work fetched successfully',
        data=work,
        count=1
    )

@work_bp.route('/getNovelsByAuthorId', methods=['GET'])
@handle_errors
def get_novels_by_author_id():
    """根据author_id获取work(novel)列表"""
    validate_required_fields(request.args, ['author_id'])
    author_id = request.args.get('author_id')
    status = request.args.get('status', None)
    limit = request.args.get('limit', 100)
    offset = request.args.get('offset', 0)

    works = MySQLService.fetch_works_by_author_id(author_id, status, limit, offset)
    return api_response(
        success=True,
        message='Works fetched successfully',
        data=works,
        count=len(works)
    )

@work_bp.route('/deleteNovelById', methods=['POST'])
@handle_errors
def delete_novel():
    """删除work(novel)"""
    data = get_request_json()
    validate_required_fields(data, ['work_id'])
    work_id = data['work_id']
    
    deleted = MySQLService.delete_work(work_id)
    if not deleted:
        return error_response('Failed to delete novel', 500)
    
    try:
        MongoService.delete_work_details(work_id)
    except Exception as e:
        logger.error(f"Error deleting work details: {str(e)}")

    return api_response(
        success=True,
        message='Work deleted successfully',
        data=None,
        count=1
    )

# ---------- work_details关联操作 ----------
@work_bp.route('/addAssetToNovel', methods=['POST'])
@handle_errors
def add_asset_to_novel():
    """将asset关联到work(novel)"""
    data = get_request_json()
    validate_required_fields(data, ['work_id', 'asset_id'])

    work_id = data['work_id']
    asset_id = data['asset_id']
    
    # 验证asset是否存在
    asset = get_asset_by_id(asset_id)
    if not asset:
        return error_response('Asset not found', 404)
    
    try:
        updated = MongoService.add_asset_to_work(work_id, asset_id)
        if not updated:
            MongoService.insert_work_details(work_id, asset_ids=[asset_id], chapter_ids=[])
    except Exception as e:
        logger.error(f"Error adding asset to work: {str(e)}")
        return error_response('Failed to add asset to work', 500)
    
    work_details = MongoService.fetch_work_details(work_id)
    return api_response(
        success=True,
        message='Asset added to work successfully',
        data={'work_id': work_id, 'asset_ids': work_details['asset_ids'] if work_details else []},
        count=1
    )

@work_bp.route('/getAssetsByWorkId', methods=['GET'])
@handle_errors
def get_assets_by_work_id():
    """根据work_id获取关联的asset列表"""
    validate_required_fields(request.args, ['work_id'])
    work_id = request.args.get('work_id')

    work_details = MongoService.fetch_work_details(work_id)
    if not work_details:
        return error_response('Work details not found', 404)
    
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
        asset_info = get_asset_by_id(asset_id)
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

@work_bp.route('/removeAssetFromNovel', methods=['POST'])
@handle_errors
def remove_asset_from_novel():
    """从work(novel)中移除asset"""
    data = get_request_json()
    validate_required_fields(data, ['work_id', 'asset_id'])

    work_id = data['work_id']
    asset_id = data['asset_id']

    try:
        removed = MongoService.remove_asset_from_work(work_id, asset_id)
        if not removed:
            return error_response('Failed to remove asset from work', 500)
    except Exception as e:
        logger.error(f"Error removing asset from work: {str(e)}")
        return error_response('Failed to remove asset from work', 500)

    work_details = MongoService.fetch_work_details(work_id)
    return api_response(
        success=True,
        message='Asset removed from work successfully',
        data={'work_id': work_id, 'asset_ids': work_details['asset_ids'] if work_details else []},
        count=1
    )