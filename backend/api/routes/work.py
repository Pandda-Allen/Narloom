# api/routes/work.py
import supabase
from flask import Blueprint, request
from utils.response_helper import error_response, api_response

work_bp = Blueprint('work', __name__)

@work_bp.route('/', methods=['POST'])
def create_work():
    """创建新的work"""
    data = request.get_json()
    
    required_fields = ['title', 'user_id']
    for field in required_fields:
        if not data.get(field):
            return error_response(f'Missing required field: {field}', 400)
    
    try:
        work_data = {
            'title': data.get('title'),
            'description': data.get('description', ''),
            'user_id': data.get('user_id'),
            'work_type': data.get('work_type', 'story'),  # story, novel, script, etc.
            'genre': data.get('genre', []),
            'tags': data.get('tags', []),
            'status': data.get('status', 'draft'),  # draft, in_progress, completed, published
            'content': data.get('content', {}),
            'settings': data.get('settings', {}),
            'characters': data.get('characters', []),
            'locations': data.get('locations', []),
            'word_count': data.get('word_count', 0),
            'visibility': data.get('visibility', 'private'),  # private, public, unlisted
            'created_at': data.get('created_at', 'now()'),
            'updated_at': data.get('updated_at', 'now()')
        }
        
        # 插入到Supabase
        response = supabase.table('works').insert(work_data).execute()
        
        if response and 'data' in response and len(response['data']) > 0:
            return api_response(
                success=True,
                message='Work created successfully',
                data=response['data'][0]
            )
        else:
            return error_response('Failed to create work', 500)
            
    except Exception as e:
        return error_response(f'Error creating work: {str(e)}', 500)

@work_bp.route('/', methods=['GET'])
def get_works():
    """获取work列表，支持多种查询条件"""
    # 获取查询参数
    user_id = request.args.get('user_id')
    work_type = request.args.get('type')
    status = request.args.get('status')
    genre = request.args.get('genre')
    search = request.args.get('search')
    limit = request.args.get('limit', default=50, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    try:
        query = supabase.table('works').select('*')
        
        # 添加筛选条件
        if user_id:
            query = query.eq('user_id', user_id)
        if work_type:
            query = query.eq('work_type', work_type)
        if status:
            query = query.eq('status', status)
        if genre:
            query = query.contains('genre', [genre])
        if search:
            query = query.ilike('title', f'%{search}%')
        
        # 排序和分页
        query = query.order('updated_at', desc=True).limit(limit).offset(offset)
        
        response = query.execute()
        
        if response and 'data' in response:
            return api_response(
                success=True,
                message='Works retrieved successfully',
                data=response['data']
            )
        else:
            return error_response('No works found', 404)
            
    except Exception as e:
        return error_response(f'Error retrieving works: {str(e)}', 500)

@work_bp.route('/<work_id>', methods=['GET'])
def get_work(work_id):
    """获取单个work详情"""
    try:
        response = supabase.table('works').select('*').eq('id', work_id).execute()
        
        if response and 'data' in response and len(response['data']) > 0:
            return api_response(
                success=True,
                message='Work retrieved successfully',
                data=response['data'][0]
            )
        else:
            return error_response('Work not found', 404)
            
    except Exception as e:
        return error_response(f'Error retrieving work: {str(e)}', 500)

@work_bp.route('/<work_id>', methods=['PUT'])
def update_work(work_id):
    """更新work"""
    data = request.get_json()
    
    try:
        update_data = {
            'title': data.get('title'),
            'description': data.get('description'),
            'work_type': data.get('work_type'),
            'genre': data.get('genre'),
            'tags': data.get('tags'),
            'status': data.get('status'),
            'content': data.get('content'),
            'settings': data.get('settings'),
            'characters': data.get('characters'),
            'locations': data.get('locations'),
            'word_count': data.get('word_count'),
            'visibility': data.get('visibility'),
            'updated_at': 'now()'
        }
        
        # 移除None值
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        response = supabase.table('works').update(update_data).eq('id', work_id).execute()
        
        if response and 'data' in response:
            return api_response(
                success=True,
                message='Work updated successfully',
                data=response['data'][0]
            )
        else:
            return error_response('Work not found', 404)
            
    except Exception as e:
        return error_response(f'Error updating work: {str(e)}', 500)

@work_bp.route('/<work_id>', methods=['DELETE'])
def delete_work(work_id):
    """删除work"""
    try:
        response = supabase.table('works').delete().eq('id', work_id).execute()
        
        if response and 'data' in response:
            return api_response(
                success=True,
                message='Work deleted successfully',
                data={}
            )
        else:
            return error_response('Work not found', 404)
            
    except Exception as e:
        return error_response(f'Error deleting work: {str(e)}', 500)

@work_bp.route('/<work_id>/stats', methods=['GET'])
def get_work_stats(work_id):
    """获取work的统计信息"""
    try:
        # 获取work基础信息
        work_response = supabase.table('works').select('*').eq('id', work_id).execute()
        
        if not work_response or 'data' not in work_response or len(work_response['data']) == 0:
            return error_response('Work not found', 404)
        
        work = work_response['data'][0]
        
        # 这里可以添加更多的统计逻辑，例如：
        # - 字数统计
        # - 章节数量
        # - 引用资源数量等
        
        stats = {
            'work_id': work_id,
            'title': work['title'],
            'word_count': work.get('word_count', 0),
            'character_count': len(work.get('characters', [])),
            'location_count': len(work.get('locations', [])),
            'created_at': work.get('created_at'),
            'updated_at': work.get('updated_at'),
            'status': work.get('status')
        }
        
        return api_response(
            success=True,
            message='Work stats retrieved successfully',
            data=stats
        )
            
    except Exception as e:
        return error_response(f'Error retrieving work stats: {str(e)}', 500)