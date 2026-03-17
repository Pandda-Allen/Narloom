# api/routes/chapter.py
"""
章节路由模块
统一使用 MySQL/MongoDB 存储
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from services.mysql_service import MySQLService
from services.mongo_service import MongoService
import logging
from utils.general_helper import handle_errors, get_request_json, validate_required_fields

chapter_bp = Blueprint('chapter', __name__)
logger = logging.getLogger(__name__)

def fetch_chapter_data(data):
    return {
        'work_id': data.get('work_id'),
        'author_id': data.get('author_id'),
        'chapter_number': data.get('chapter_number'),
        'chapter_title': data.get('chapter_title', ''),
        'content': data.get('content', ''),
        'status': data.get('status', 'draft'),
        'word_count': data.get('word_count', 0),
        'description': data.get('description', ''),
    }

@chapter_bp.route('/createChapter', methods=['POST'])
@handle_errors
def create_chapter():
    """创建新的章节"""
    data = get_request_json()
    validate_required_fields(data, ['work_id', 'author_id', 'chapter_number'])

    chapter_data = fetch_chapter_data(data)

    # 插入 MySQL chapters
    try:
        chapter = MySQLService().insert_chapter(**chapter_data)
        chapter_id = chapter['chapter_id']
        work_id = chapter_data.get('work_id')
    except Exception as e:
        logger.error(f"Error inserting chapter: {str(e)}")
        return error_response('Failed to insert chapter', 500)

    # 更新 MongoDB work_details
    try:
        updated = MongoService().add_chapter_to_work(work_id, chapter_id)
        if not updated:
            logger.warning(f"Work details not found for work {work_id}, creating new")
            MongoService().insert_work_details(work_id, chapter_ids=[chapter_id], asset_ids=[])
    except Exception as e:
        logger.error(f"Error updating work details: {str(e)}")
        # 回滚：删除 MySQL 中的章节
        MySQLService().delete_chapter(chapter_id)
        return error_response('Failed to update work details', 500)

    # 返回完整的章节信息
    full_chapter = MySQLService().fetch_chapter_by_id(chapter_id)
    return api_response(
        success=True,
        message='Chapter created successfully',
        data=full_chapter,
        count=1
    )

@chapter_bp.route('/updateChapterById', methods=['POST'])
@handle_errors
def update_chapter():
    """更新章节"""
    data = get_request_json()
    validate_required_fields(data, ['chapter_id'])

    chapter_id = data.get('chapter_id')
    update_fields = {}
    if 'chapter_number' in data:
        update_fields['chapter_number'] = data['chapter_number']
    if 'chapter_title' in data:
        update_fields['chapter_title'] = data['chapter_title']
    if 'content' in data:
        update_fields['content'] = data['content']
    if 'status' in data:
        update_fields['status'] = data['status']
    if 'word_count' in data:
        update_fields['word_count'] = data['word_count']
    if 'description' in data:
        update_fields['description'] = data['description']

    if not update_fields:
        return error_response('No fields to update', 400)

    updated = MySQLService().update_chapter(chapter_id, update_fields)
    if not updated:
        return error_response('Failed to update chapter', 500)

    return api_response(
        success=True,
        message='Chapter updated successfully',
        data=updated,
        count=1
    )

@chapter_bp.route('/getChapterByNovelId', methods=['GET'])
@handle_errors
def get_chapter_by_novel_id():
    """根据 novel_id 获取章节列表"""
    validate_required_fields(request.args, ['work_id'])
    work_id = request.args.get('work_id')
    status = request.args.get('status')
    limit_str = request.args.get('limit', '100')
    offset_str = request.args.get('offset', '0')

    try:
        limit = int(limit_str)
        offset = int(offset_str)
    except ValueError:
        return error_response('limit and offset must be integers', 400)

    if limit < 0 or offset < 0:
        return error_response('limit and offset must be non-negative integers', 400)

    if limit > 1000:
        limit = 1000

    chapters = MySQLService().fetch_chapters_by_work_id(work_id, status, limit, offset)
    return api_response(
        success=True,
        message='Chapters fetched successfully',
        data=chapters,
        count=len(chapters)
    )

@chapter_bp.route('/deleteChapterById', methods=['POST'])
@handle_errors
def delete_chapter():
    """删除章节"""
    data = get_request_json()
    validate_required_fields(data, ['chapter_id'])
    chapter_id = data.get('chapter_id')

    chapter = MySQLService().fetch_chapter_by_id(chapter_id)
    if not chapter:
        return error_response('Chapter not found', 404)
    work_id = chapter['work_id']

    # 删除 MySQL 中的章节
    deleted = MySQLService().delete_chapter(chapter_id)
    if not deleted:
        return error_response('Chapter not found', 404)

    # 从 MongoDB work_details 中移除 chapter_id
    try:
        MongoService().remove_chapter_from_work(work_id, chapter_id)
    except Exception as e:
        logger.error(f"Error updating work details after chapter deletion: {str(e)}")

    return api_response(
        success=True,
        message='Chapter deleted successfully',
        data=None,
        count=1
    )
