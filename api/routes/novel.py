# api/routes/novel.py
"""
Novel 路由模块（原 Chapter 模块）
统一使用 MySQL/MongoDB 存储
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors
from utils.general_helper import validate_required_fields
from utils.resource_helper import (
    build_novel_data,
    parse_pagination_args,
    delete_novel_cascade
)
from db import MySQLService, MongoService
import logging

novel_bp = Blueprint('novel', __name__)
logger = logging.getLogger(__name__)


@novel_bp.route('/createNovel', methods=['POST'])
@handle_errors
def create_novel():
    """创建新的 novel 章节"""
    data = request.get_json()
    validate_required_fields(data, ['work_id', 'author_id', 'novel_number'])

    novel_data = build_novel_data(data)

    try:
        novel = MySQLService().insert_novel(**novel_data)
        novel_id = novel['novel_id']
        work_id = novel_data.get('work_id')
    except Exception as e:
        logger.error(f"Error inserting novel: {str(e)}")
        return error_response('Failed to insert novel', 500)

    try:
        updated = MongoService().add_chapter_to_work(work_id, novel_id)
        if not updated:
            logger.warning(f"Work details not found for work {work_id}, creating new")
            MongoService().insert_work_details(work_id, chapter_ids=[novel_id], asset_ids=[])
    except Exception as e:
        logger.error(f"Error updating work details: {str(e)}")
        MySQLService().delete_novel(novel_id)
        return error_response('Failed to update work details', 500)

    full_novel = MySQLService().fetch_novel_by_id(novel_id)
    return api_response(
        success=True,
        message='Novel created successfully',
        data=full_novel,
        count=1
    )


@novel_bp.route('/updateNovelById', methods=['POST'])
@handle_errors
def update_novel():
    """更新 novel 章节"""
    data = request.get_json()
    validate_required_fields(data, ['novel_id'])

    novel_id = data.get('novel_id')
    update_fields = {}

    allowed_fields = ['novel_number', 'novel_title', 'content', 'status', 'word_count', 'description']
    for field in allowed_fields:
        if field in data:
            update_fields[field] = data[field]

    if not update_fields:
        return error_response('No fields to update', 400)

    updated = MySQLService().update_novel(novel_id, update_fields)
    if not updated:
        return error_response('Failed to update novel', 500)

    return api_response(
        success=True,
        message='Novel updated successfully',
        data=updated,
        count=1
    )


@novel_bp.route('/getNovelByWorkId', methods=['GET'])
@handle_errors
def get_novel_by_work_id():
    """根据 work_id 获取 novel 章节列表"""
    validate_required_fields(request.args, ['work_id'])
    work_id = request.args.get('work_id')
    status = request.args.get('status')

    try:
        limit, offset = parse_pagination_args(request.args)
    except ValueError as e:
        return error_response(str(e), 400)

    novels = MySQLService().fetch_novels_by_work_id(work_id, status, limit, offset)
    return api_response(
        success=True,
        message='Novels fetched successfully',
        data=novels,
        count=len(novels)
    )


@novel_bp.route('/deleteNovelById', methods=['POST'])
@handle_errors
def delete_novel():
    """删除 novel 章节"""
    data = request.get_json()
    validate_required_fields(data, ['novel_id'])
    novel_id = data.get('novel_id')

    deleted, _ = delete_novel_cascade(novel_id)

    if deleted:
        return api_response(
            success=True,
            message='Novel deleted successfully',
            data=None,
            count=1
        )
    return error_response('Novel not found', 404)
