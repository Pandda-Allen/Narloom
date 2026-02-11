# api/routes/chapter.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response, format_supabase_response
from services.supabase_service import SupabaseService
import json
from datetime import datetime

chapter_bp = Blueprint('chapter', __name__)

def fetch_chapter_data(data):
    try:
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
        chapter_data = {k: v for k, v in chapter_data.items() if v is not None}
        return chapter_data
    except Exception as e:
        raise ValueError(f"Error reading chapter data: {str(e)}")

@chapter_bp.route('/createChapter', methods=['POST'])
def create_chapter():
    """创建新的chapter(novel)"""
    try:
        data = request.get_json()

        if not data:
            return error_response('No data provided', 400)
        
        if not data.get('novel_id') or not data.get('author_id'):
            return error_response('Novel ID and author ID are required', 400)

        # 从请求数据中提取novel信息
        chapter_data = fetch_chapter_data(data)
        chapter_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not chapter_data:
            return error_response('Invalid chapter data', 400)
        # 插入到Supabase
        response = SupabaseService().chapter_create(chapter_data)

        # 格式化响应
        formatted_response = format_supabase_response(response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message='Chapter created successfully',
                data=formatted_response['data'][0],
                count=formatted_response.get('count')
            )
        else:
            return error_response('Failed to create chapter', 500)
            
    except Exception as e:
        return error_response(f'Error creating chapter: {str(e)}', 500)

@chapter_bp.route('/updateChapterById', methods=['POST'])
def update_chapter():
    """更新chapter"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided', 400)
        
        chapter_id = data.get('chapter_id')

        if not chapter_id:
            return error_response('chapter_id is required', 400)

        # 读取数据
        chapter_data = fetch_chapter_data(data)
        if not chapter_data:
            return error_response('Failed to read chapter data', 400)
                
        # 插入到Supabase
        response = SupabaseService().chapter_update(chapter_id, chapter_data)

        # 格式化响应
        formatted_response = format_supabase_response(response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message='Chapter updated successfully',
                data=formatted_response['data'][0]
            )
        else:
            return error_response('Failed to update chapter', 500)
            
    except ValueError as e:
        return error_response(f'Error processing request: {str(e)}', 400)
    except Exception as e:
        return error_response(f'Error updating chapter: {str(e)}', 500)
    
@chapter_bp.route('/getChapterByNovelId', methods=['POST'])
def get_chapter_by_novel_id():
    """根据novel_id获取chapter列表"""
    try:
        data = request.get_json()
        if not data:
            return error_response('No data provided', 400)
        
        novel_id = data.get('novel_id')
        if not novel_id:
            return error_response('novel_id is required', 400)

        response = SupabaseService().chapter_fetch_by_novel_id(novel_id)

        formatted_response = format_supabase_response(response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True, 
                message='Chapters fetched successfully', 
                data=formatted_response.get('data'),
                count=formatted_response.get('count')
            )
        else:
            return error_response('Failed to fetch chapters', 500)
        
    except Exception as e:
        return error_response(f'Error fetching chapters: {str(e)}', 500)