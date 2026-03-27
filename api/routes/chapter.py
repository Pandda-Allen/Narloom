# api/routes/chapter.py
"""
章节路由模块
统一使用 MySQL/MongoDB 存储
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors
from utils.general_helper import validate_required_fields
from utils.resource_helper import (
    build_chapter_data,
    parse_pagination_args,
    delete_chapter_cascade
)
from services.db import MySQLService, MongoService
import logging

chapter_bp = Blueprint('chapter', __name__)
logger = logging.getLogger(__name__)


@chapter_bp.route('/createChapter', methods=['POST'])
@handle_errors
def create_chapter():
    """创建新的章节"""
    data = request.get_json()
    validate_required_fields(data, ['work_id', 'author_id', 'chapter_number'])

    chapter_data = build_chapter_data(data)

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
    data = request.get_json()
    validate_required_fields(data, ['chapter_id'])

    chapter_id = data.get('chapter_id')
    update_fields = {}

    # 允许更新的字段列表
    allowed_fields = ['chapter_number', 'chapter_title', 'content', 'status', 'word_count', 'description']
    for field in allowed_fields:
        if field in data:
            update_fields[field] = data[field]

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

    try:
        limit, offset = parse_pagination_args(request.args)
    except ValueError as e:
        return error_response(str(e), 400)

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
    data = request.get_json()
    validate_required_fields(data, ['chapter_id'])
    chapter_id = data.get('chapter_id')

    deleted, _ = delete_chapter_cascade(chapter_id)

    if deleted:
        return api_response(
            success=True,
            message='Chapter deleted successfully',
            data=None,
            count=1
        )
    return error_response('Chapter not found', 404)
