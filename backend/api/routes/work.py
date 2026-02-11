# api/routes/work.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response, format_supabase_response
from utils.general_helper import handle_errors, get_request_json, validate_required_fields
from services.supabase_service import SupabaseService
import json
from datetime import datetime

work_bp = Blueprint('work', __name__)

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
        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
    novel_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    response = SupabaseService().novel_create(novel_data)
    formatted = format_supabase_response(response)

    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True,
            message='Work created successfully',
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Failed to create work', 500)

@work_bp.route('/updateNovelById', methods=['POST'])
def update_novel():
    """更新work(novel)"""
    data = get_request_json()
    validate_required_fields(data, ['novel_id'])

    novel_id = data.get('novel_id')
    novel_data = fetch_novel_data(data)

    response = SupabaseService().novel_update(novel_id, novel_data)
    formatted = format_supabase_response(response)

    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True,
            message='Work updated successfully',
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Failed to update work', 500)
    
@work_bp.route('/getNovelById', methods=['GET'])
@handle_errors
def get_novel():
    """获取单个work(novel)详情"""
    validate_required_fields(request.args, ['novel_id'])

    response = SupabaseService().novel_get_by_id(
        request.args.get('novel_id')
    )
    formatted = format_supabase_response(response)

    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True,
            message='Work retrieved successfully',
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Work not found', 404)