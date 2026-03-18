from flask import request
from functools import wraps
from utils.response_helper import error_response

# 注意：handle_errors 装饰器已移至 utils.decorators
# 为了向后兼容，这里保留导入引用
from utils.decorators import handle_errors


# ---------- 通用辅助函数 ----------
def get_request_json():
    """获取并验证请求的 JSON 数据"""
    data = request.get_json()
    if data is None:
        raise ValueError("No data provided")
    return data


def validate_required_fields(data, required_fields):
    """检查必需字段是否存在"""
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
