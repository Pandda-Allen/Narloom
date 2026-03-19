from flask import Blueprint, request, jsonify, current_app
from services.ai_service import qwen_ai_service
from utils.response_helper import api_response
from utils.general_helper import handle_errors, get_request_json, validate_required_fields
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/process', methods=['POST'])
@handle_errors
def process_ai_request():
    """处理 AI 请求"""
    data = get_request_json()

    # 检查 AI 服务是否已初始化
    if not qwen_ai_service._initialized:
        return api_response(
            success=False,
            message='AI Service not initialized. Please check DASHSCOPE_API_KEY configuration.',
            status_code=503
        )

    # 处理请求
    result = qwen_ai_service.process_request(data)

    # 记录使用情况
    if result.get('success'):
        current_app.logger.info(f"AI task completed: {result.get('task_id')}")

    # 添加请求信息
    result['endpoint'] = '/ai/process'
    result['request_timestamp'] = datetime.now().isoformat()

    status_code = 200 if result.get('success') else 500
    return jsonify(result), status_code

@ai_bp.route('/models', methods=['GET'])
@handle_errors
def get_models():
    """获取支持的 AI 模型列表"""
    models = qwen_ai_service.get_supported_models()
    return api_response(
        success=True,
        message='Models fetched successfully',
        data={'models': models},
        count=len(models)
    )

@ai_bp.route('/health', methods=['GET'])
@handle_errors
def health_check():
    """健康检查"""
    health_status = qwen_ai_service.health_check()

    return api_response(
        success=True,
        message='Health check completed',
        data={
            'service': 'qwen-ai',
            **health_status
        }
    )

@ai_bp.route('/test', methods=['POST'])
@handle_errors
def test_ai():
    """测试 AI 接口"""
    test_data = {
        "task_type": "chat",
        "model": "qwen3.5-plus",
        "content": {
            "user_prompt": "请用一句话介绍一下你自己"
        }
    }

    result = qwen_ai_service.process_request(test_data)

    return api_response(
        success=result.get('success', False),
        message='AI test completed' if result.get('success') else 'AI test failed',
        data={'test_result': result}
    )

@ai_bp.route('/capabilities', methods=['GET'])
@handle_errors
def get_capabilities():
    """获取 AI 服务能力"""
    return api_response(
        success=True,
        message='Capabilities fetched successfully',
        data={
            'capabilities': {
                'supported_tasks': [
                    'chat', 'enhance', 'abstract', 'generate',
                    'translate', 'summarize', 'rewrite', 'code', 'analysis'
                ],
                'supported_languages': ['zh-CN', 'en-US', 'ja-JP', 'ko-KR', 'fr-FR', 'es-ES', 'de-DE', 'ru-RU'],
                'max_tokens': 16384,
                'supports_streaming': True,
                'provider': '阿里云通义千问',
                'api_version': 'v1'
            }
        }
    )
