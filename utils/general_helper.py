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
    """
    检查必需字段是否存在且非空

    参数:
        data: 数据字典
        required_fields: 必需字段名列表

    异常:
        ValueError: 当缺少必需字段时抛出

    返回:
        None

    使用示例:
        data = request.get_json()
        validate_required_fields(data, ['user_id', 'work_id'])
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    if not isinstance(required_fields, (list, tuple)):
        raise ValueError("required_fields must be a list or tuple")

    missing = [field for field in required_fields if field not in data or data.get(field) is None or data.get(field) == '']
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def validate_field_type(value, field_name: str, expected_type: type, allow_none: bool = False):
    """
    验证字段类型

    参数:
        value: 要验证的值
        field_name: 字段名称 (用于错误消息)
        expected_type: 期望的类型
        allow_none: 是否允许 None 值

    异常:
        ValueError: 当类型不匹配时抛出
    """
    if value is None:
        if allow_none:
            return
        raise ValueError(f"Field '{field_name}' cannot be None")

    if not isinstance(value, expected_type):
        raise ValueError(
            f"Field '{field_name}' must be of type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )


def sanitize_string(value: str, max_length: int = None, allow_empty: bool = False) -> str:
    """
    清理字符串输入

    参数:
        value: 要清理的字符串
        max_length: 最大长度限制
        allow_empty: 是否允许空字符串

    返回:
        清理后的字符串

    异常:
        ValueError: 当输入无效时抛出
    """
    if not isinstance(value, str):
        raise ValueError("Value must be a string")

    cleaned = value.strip()

    if not cleaned and not allow_empty:
        raise ValueError("String cannot be empty")

    if max_length and len(cleaned) > max_length:
        raise ValueError(f"String exceeds maximum length of {max_length} characters")

    return cleaned
