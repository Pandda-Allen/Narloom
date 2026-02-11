from flask import request
from functools import wraps


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
            return error_response(str(ve), 400)
        except Exception as e:
            return error_response(f"Internal error: {str(e)}", 500)
    return decorated