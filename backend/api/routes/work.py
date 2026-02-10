# api/routes/work.py
from flask import Blueprint, request
from utils.response_helper import error_response, api_response, format_supabase_response
from services.supabase_service import SupabaseService
import json
from datetime import datetime

work_bp = Blueprint('work', __name__)


def fetch_novel_data(data):
    try:
        novel_data = {
            'author_id': data.get('author_id'),
            'novel_id': data.get('novel_id', None),
            'title': data.get('title'),
            'genre': data.get('genre', ''),
            'tags': data.get('tags', []),
            'status': data.get('status', 'draft'),  # draft, in_progress, completed, published
            'content': data.get('content', ''),
            'word_count': data.get('word_count', 0),
            'created_at': data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'description': data.get('description', ''),
        }
        # 移除空值字段
        novel_data = {k: v for k, v in novel_data.items() if v is not None}
        return novel_data
    except Exception as e:
        raise ValueError(f"Error reading novel data: {str(e)}")

@work_bp.route('/createNovel', methods=['POST'])
def create_novel():
    """创建新的work(novel)"""
    try:
        data = request.get_json()

        if not data:
            return error_response('No data provided', 400)

        # 从请求数据中提取novel信息
        novel_data = fetch_novel_data(data)

        if not novel_data:
            return error_response('Invalid work data', 400)

        # 插入到Supabase
        response = SupabaseService().novel_create(novel_data)

        # 格式化响应
        formatted_response = format_supabase_response(response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message='Work created successfully',
                data=formatted_response['data'][0],
                count=formatted_response.get('count')
            )
        else:
            return error_response('Failed to create work', 500)
            
    except Exception as e:
        return error_response(f'Error creating work: {str(e)}', 500)

@work_bp.route('/updateNovelById', methods=['POST'])
def update_novel():
    """更新work(novel)"""
    try:
        data = request.get_json()

        if not data:
            return error_response('No data provided', 400)

        novel_id = data.get('novel_id')
        if not novel_id:
            return error_response('Novel ID is required', 400)

        # 从请求数据中提取novel信息
        novel_data = fetch_novel_data(data)

        if not novel_data:
            return error_response('Invalid work data', 400)

        # 更新到Supabase
        response = SupabaseService().novel_update(novel_id, novel_data)
        
        # 格式化响应
        formatted_response = format_supabase_response(response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message='Work updated successfully',
                data=formatted_response['data'][0],
                count=formatted_response.get('count')
            )
        else:
            return error_response('Failed to update work', 500)
            
    except Exception as e:
        return error_response(f'Error updating work: {str(e)}', 500)
    
@work_bp.route('/getNovelById', methods=['GET'])
def get_novel():
    """获取单个work(novel)详情"""
    try:
        novel_id = request.args.get('novel_id')
        if not novel_id:
            return error_response('Novel ID is required', 400)

        # 从Supabase获取novel信息
        response = SupabaseService().novel_get_by_id(novel_id)

        # 格式化响应
        formatted_response = format_supabase_response(response)

        if formatted_response and formatted_response.get('count', 0) > 0:
            return api_response(
                success=True,
                message='Work retrieved successfully',
                data=formatted_response['data'][0],
                count=formatted_response.get('count')
            )
        else:
            return error_response('Work not found', 404)
            
    except Exception as e:
        return error_response(f'Error retrieving work: {str(e)}', 500)