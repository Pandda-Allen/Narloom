"""
自定义装饰器模块
提供常用的装饰器功能
"""
from functools import wraps
from flask import request, current_app
import logging

from utils.response_helper import error_response, api_response


def handle_errors(f):
    """统一异常处理装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as ve:
            # 业务验证错误，返回具体信息给客户端
            return error_response(str(ve), 400)
        except Exception as e:
            # 系统错误，记录日志但不暴露内部信息
            logger = logging.getLogger(__name__)
            logger.error(f"Internal server error in {f.__name__}: {str(e)}", exc_info=True)
            return error_response("Internal server error", 500)
    return decorated


def validate_json_request(*required_fields):
    """验证 JSON 请求必需字段的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if data is None:
                return error_response("Request body must be JSON", 400)

            missing = [field for field in required_fields if field not in data or not data[field]]
            if missing:
                return error_response(f"Missing required fields: {', '.join(missing)}", 400)

            # 将解析后的数据存入 request 上下文，供后续使用
            request.json_data = data
            return f(*args, **kwargs)
        return decorated
    return decorator


def log_api_call(f):
    """记录 API 调用的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.info(f"API call: {request.method} {request.path}")
        result = f(*args, **kwargs)
        logger.info(f"API response: {result[1] if isinstance(result, tuple) else 200}")
        return result
    return decorated


def service_initialized(service_instance):
    """检查服务是否已初始化的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not service_instance._initialized:
                service_name = service_instance.__class__.__name__
                return error_response(f"{service_name} not initialized", 503)
            return f(*args, **kwargs)
        return decorated
    return decorator
