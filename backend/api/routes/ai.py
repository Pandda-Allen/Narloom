from flask import Blueprint, request, jsonify, current_app
from services.ai_service import ai_service
from utils.response_helper import error_response, api_response
import time

# 创建蓝图
ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.before_request
def before_request():
    """记录请求日志"""
    current_app.logger.info(f"AI请求: {request.method} {request.path}")

@ai_bp.route('/enhance', methods=['POST'])
def enhance_content():
    """
    美化小说内容
    POST数据格式:
    {
        "content": "小说内容文本",
        "style": "优美流畅"  # 可选，默认优美流畅
    }
    """
    data = request.get_json()
    
    if not data or 'content' not in data:
        return error_response('请提供小说内容', 400)
    
    content = data.get('content', '').strip()
    style = data.get('style', '优美流畅')
    
    if not content:
        return error_response('小说内容不能为空', 400)
    
    # 验证内容长度
    if len(content) > 10000:  # 限制内容长度
        return error_response('小说内容过长，请限制在10000字以内', 400)
    
    try:
        start_time = time.time()
        result = ai_service.enhance_content(content, style)
        processing_time = time.time() - start_time
        
        if result.get('success'):
            return api_response(
                success=True,
                message='内容美化成功',
                data={
                    'enhanced_content': result['data'].get('result', ''),
                    'original_length': len(content),
                    'processing_time': round(processing_time, 2),
                    'usage': result.get('usage', {})
                }
            )
        else:
            return error_response(result.get('error', 'AI处理失败'), 500)
            
    except Exception as e:
        current_app.logger.error(f"内容美化失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@ai_bp.route('/refine', methods=['POST'])
def refine_content():
    """
    提炼小说内容
    POST数据格式:
    {
        "content": "小说内容文本",
        "target_length": "简洁"  # 可选：简洁/中等/详细，默认简洁
    }
    """
    data = request.get_json()
    
    if not data or 'content' not in data:
        return error_response('请提供小说内容', 400)
    
    content = data.get('content', '').strip()
    target_length = data.get('target_length', '简洁')
    
    if not content:
        return error_response('小说内容不能为空', 400)
    
    if len(content) > 10000:
        return error_response('小说内容过长，请限制在10000字以内', 400)
    
    try:
        start_time = time.time()
        result = ai_service.refine_content(content, target_length)
        processing_time = time.time() - start_time
        
        if result.get('success'):
            return api_response(
                success=True,
                message='内容提炼成功',
                data={
                    'refined_content': result['data'].get('result', ''),
                    'original_length': len(content),
                    'target_length': target_length,
                    'processing_time': round(processing_time, 2),
                    'usage': result.get('usage', {})
                }
            )
        else:
            return error_response(result.get('error', 'AI处理失败'), 500)
            
    except Exception as e:
        current_app.logger.error(f"内容提炼失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@ai_bp.route('/extract', methods=['POST'])
def extract_key_info():
    """
    提取关键信息
    POST数据格式:
    {
        "content": "小说内容文本"
    }
    """
    data = request.get_json()
    
    if not data or 'content' not in data:
        return error_response('请提供小说内容', 400)
    
    content = data.get('content', '').strip()
    
    if not content:
        return error_response('小说内容不能为空', 400)
    
    if len(content) > 10000:
        return error_response('小说内容过长，请限制在10000字以内', 400)
    
    try:
        start_time = time.time()
        result = ai_service.extract_key_info(content)
        processing_time = time.time() - start_time
        
        if result.get('success'):
            return api_response(
                success=True,
                message='关键信息提取成功',
                data={
                    'key_info': result['data'],
                    'original_length': len(content),
                    'processing_time': round(processing_time, 2),
                    'usage': result.get('usage', {})
                }
            )
        else:
            return error_response(result.get('error', 'AI处理失败'), 500)
            
    except Exception as e:
        current_app.logger.error(f"关键信息提取失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@ai_bp.route('/analyze-style', methods=['POST'])
def analyze_writing_style():
    """
    分析写作风格
    POST数据格式:
    {
        "content": "小说内容文本"
    }
    """
    data = request.get_json()
    
    if not data or 'content' not in data:
        return error_response('请提供小说内容', 400)
    
    content = data.get('content', '').strip()
    
    if not content:
        return error_response('小说内容不能为空', 400)
    
    if len(content) > 5000:  # 风格分析可以处理稍短的内容
        return error_response('内容过长，请限制在5000字以内进行风格分析', 400)
    
    try:
        start_time = time.time()
        result = ai_service.analyze_style(content)
        processing_time = time.time() - start_time
        
        if result.get('success'):
            return api_response(
                success=True,
                message='写作风格分析成功',
                data={
                    'style_analysis': result['data'],
                    'original_length': len(content),
                    'processing_time': round(processing_time, 2),
                    'usage': result.get('usage', {})
                }
            )
        else:
            return error_response(result.get('error', 'AI处理失败'), 500)
            
    except Exception as e:
        current_app.logger.error(f"写作风格分析失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@ai_bp.route('/continue', methods=['POST'])
def continue_writing():
    """
    续写小说内容
    POST数据格式:
    {
        "content": "小说内容文本",
        "length": 200  # 可选，续写长度（字数）
    }
    """
    data = request.get_json()
    
    if not data or 'content' not in data:
        return error_response('请提供小说内容', 400)
    
    content = data.get('content', '').strip()
    length = data.get('length', 200)
    
    if not content:
        return error_response('小说内容不能为空', 400)
    
    if len(content) > 5000:
        return error_response('续写内容过长，请限制在5000字以内', 400)
    
    try:
        start_time = time.time()
        result = ai_service.generate_continuation(content, length)
        processing_time = time.time() - start_time
        
        if result.get('success'):
            return api_response(
                success=True,
                message='续写成功',
                data={
                    'continuation': result['data'].get('result', ''),
                    'original_content': content,
                    'requested_length': length,
                    'processing_time': round(processing_time, 2),
                    'usage': result.get('usage', {})
                }
            )
        else:
            return error_response(result.get('error', 'AI处理失败'), 500)
            
    except Exception as e:
        current_app.logger.error(f"续写失败: {str(e)}")
        return error_response('服务器内部错误', 500)

@ai_bp.route('/batch', methods=['POST'])
def batch_process():
    """
    批量处理小说内容
    POST数据格式:
    {
        "content": "小说内容文本",
        "operations": ["enhance", "refine", "extract"]  # 要执行的操作列表
    }
    """
    data = request.get_json()
    
    if not data or 'content' not in data or 'operations' not in data:
        return error_response('请提供小说内容和操作列表', 400)
    
    content = data.get('content', '').strip()
    operations = data.get('operations', [])
    
    if not content:
        return error_response('小说内容不能为空', 400)
    
    if len(content) > 5000:
        return error_response('内容过长，请限制在5000字以内', 400)
    
    if not operations:
        return error_response('请指定至少一个操作', 400)
    
    valid_operations = ['enhance', 'refine', 'extract', 'analyze-style']
    operations = [op for op in operations if op in valid_operations]
    
    if not operations:
        return error_response('没有有效的操作类型', 400)
    
    try:
        results = {}
        total_processing_time = 0
        
        for operation in operations:
            start_time = time.time()
            
            if operation == 'enhance':
                result = ai_service.enhance_content(content)
                key = 'enhanced'
            elif operation == 'refine':
                result = ai_service.refine_content(content)
                key = 'refined'
            elif operation == 'extract':
                result = ai_service.extract_key_info(content)
                key = 'extracted'
            elif operation == 'analyze-style':
                result = ai_service.analyze_style(content)
                key = 'style_analysis'
            
            processing_time = time.time() - start_time
            total_processing_time += processing_time
            
            if result.get('success'):
                results[key] = result['data']
                results[f'{key}_usage'] = result.get('usage', {})
            else:
                results[key] = {'error': result.get('error', '处理失败')}
        
        return api_response(
            success=True,
            message='批量处理完成',
            data={
                'results': results,
                'operations_performed': operations,
                'original_length': len(content),
                'total_processing_time': round(total_processing_time, 2)
            }
        )
            
    except Exception as e:
        current_app.logger.error(f"批量处理失败: {str(e)}")
        return error_response('服务器内部错误', 500)
