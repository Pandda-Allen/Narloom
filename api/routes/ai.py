from flask import Blueprint, request, jsonify, current_app
from services.ai_service import deepseek_ai_service
import json
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/process', methods=['POST'])
def process_ai_request():
    """处理AI请求"""
    try:
        data = request.get_json()
        
        # 基本验证
        if not data:
            return jsonify({
                "success": False,
                "error": "No data provided",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # 检查AI服务是否已初始化
        if not deepseek_ai_service._initialized:
            print("AI Service not initialized.")
            return jsonify({
                "success": False,
                "error": "AI Service not initialized. Please check DEEPSEEK_API_KEY configuration.",
                "timestamp": datetime.now().isoformat()
            }), 503
        
        # 处理请求
        result = deepseek_ai_service.process_request(data)
        
        # 记录使用情况
        if result.get('success'):
            print(f"AI task completed: {result.get('task_id')}")
            current_app.logger.info(f"AI task completed: {result.get('task_id')}")
        
        # 添加请求信息
        result['endpoint'] = '/ai/process'
        result['request_timestamp'] = datetime.now().isoformat()
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in AI processing: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": datetime.now().isoformat()
        }), 500

@ai_bp.route('/models', methods=['GET'])
def get_models():
    """获取支持的AI模型列表"""
    try:
        models = deepseek_ai_service.get_supported_models()
        return jsonify({
            "success": True,
            "models": models,
            "count": len(models),
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@ai_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        health_status = deepseek_ai_service.health_check()
        
        return jsonify({
            "success": True,
            "service": "deepseek-ai",
            **health_status
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "service": "deepseek-ai",
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@ai_bp.route('/test', methods=['POST'])
def test_ai():
    """测试AI接口"""
    try:
        test_data = {
            "task_type": "chat",
            "model": "deepseek-chat",
            "content": {
                "user_prompt": "请用一句话介绍一下你自己"
            }
        }
        
        result = deepseek_ai_service.process_request(test_data)
        
        return jsonify({
            "success": True,
            "test_result": result,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@ai_bp.route('/capabilities', methods=['GET'])
def get_capabilities():
    """获取AI服务能力"""
    return jsonify({
        "success": True,
        "capabilities": {
            "supported_tasks": [
                "chat", "enhance", "abstract", "generate", 
                "translate", "summarize", "rewrite", "code", "analysis"
            ],
            "supported_languages": ["zh-CN", "en-US", "ja-JP", "ko-KR", "fr-FR", "es-ES", "de-DE", "ru-RU"],
            "max_tokens": 4096,
            "supports_streaming": False,
            "provider": "DeepSeek",
            "api_version": "v1"
        },
        "timestamp": datetime.now().isoformat()
    }), 200