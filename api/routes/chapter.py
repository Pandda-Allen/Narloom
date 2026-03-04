# api/routes/chapter.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response, format_supabase_response
from services.supabase_service import SupabaseService
import json
from datetime import datetime
from utils.general_helper import handle_errors, get_request_json, validate_required_fields

chapter_bp = Blueprint('chapter', __name__)

def fetch_chapter_data(data):
    chapter_data = {
        'chapter_id': data.get('chapter_id'),
        'novel_id': data.get('novel_id'),
        'author_id': data.get('author_id'),
        'chapter_number': data.get('chapter_number'),
        'chapter_title': data.get('chapter_title'),
        'content': data.get('content', ''),
        'status': data.get('status', 'draft'),  # draft, in_progress, completed, published
        'word_count': data.get('word_count', 0),
        'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'description': data.get('description', ''),
    }
    # 移除空值字段
    return {k: v for k, v in chapter_data.items() if v is not None}

@chapter_bp.route('/createChapter', methods=['POST'])
@handle_errors
def create_chapter():
    """创建新的chapter(novel)"""
    data = get_request_json()
    validate_required_fields(data, ['novel_id', 'author_id'])

    chapter_data = fetch_chapter_data(data)
    chapter_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    response = SupabaseService().chapter_create(chapter_data)
    formatted = format_supabase_response(response)

    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True,
            message='Chapter created successfully',
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Failed to create chapter', 500)


@chapter_bp.route('/updateChapterById', methods=['POST'])
@handle_errors
def update_chapter():
    """更新chapter"""
    data = get_request_json()
    validate_required_fields(data, ['chapter_id'])
    
    chapter_id = data.get('chapter_id')
    chapter_data = fetch_chapter_data(data)
            
    response = SupabaseService().chapter_update(chapter_id, chapter_data)
    formatted = format_supabase_response(response)

    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True,
            message='Chapter updated successfully',
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Failed to update chapter', 500)
            
    
@chapter_bp.route('/getChapterByNovelId', methods=['POST'])
@handle_errors
def get_chapter_by_novel_id():
    """根据novel_id获取chapter列表"""
    data = get_request_json()
    validate_required_fields(data, ['novel_id'])
    
    novel_id = data.get('novel_id')

    response = SupabaseService().chapter_fetch_by_novel_id(novel_id)
    formatted = format_supabase_response(response)

    if formatted and formatted.get('count', 0) > 0:
        return api_response(
            success=True, 
            message='Chapters fetched successfully', 
            data=formatted['data'],
            count=formatted['count']
        )
    return error_response('Failed to fetch chapters', 500)