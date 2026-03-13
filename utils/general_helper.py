from flask import request
from functools import wraps
from utils.response_helper import error_response

# ---------- 通用辅助函数 ----------
def get_request_json():
    """获取并验证请求的JSON数据"""
    data = request.get_json()
    if data is None:
        raise ValueError("No data provided")
    return data

def validate_required_fields(data, required_fields):
    """检查必需字段是否存在"""
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

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
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Internal server error in {f.__name__}: {str(e)}", exc_info=True)
            return error_response("Internal server error", 500)
    return decorated