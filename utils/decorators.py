"""
自定义装饰器模块
提供常用的装饰器功能
"""
from functools import wraps
from flask import request, current_app, g
import logging
import jwt

from utils.response_helper import error_response, api_response


def handle_errors(f):
    """
    统一异常处理装饰器

    功能:
    - 捕获 ValueError 返回 400 业务错误
    - 捕获其他异常返回 500 内部错误，记录详细日志
    - 支持记录请求上下文信息
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as ve:
            logger = logging.getLogger(__name__)
            logger.info(f"Business validation error in {f.__name__}: {str(ve)}")
            return error_response(str(ve), 400)
        except KeyError as ke:
            logger = logging.getLogger(__name__)
            logger.warning(f"Missing key in {f.__name__}: {str(ke)}")
            return error_response(f"Missing required data: {str(ke)}", 400)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(
                f"Internal server error in {f.__name__}: {str(e)}",
                exc_info=True,
                extra={
                    'request_method': request.method,
                    'request_path': request.path,
                    'request_args': request.args.to_dict() if request.args else None
                }
            )
            return error_response("Internal server error", 500)
    return decorated


def validate_json_request(*required_fields):
    """
    验证 JSON 请求必需字段的装饰器

    功能:
    - 验证请求体为有效 JSON
    - 检查所有必需字段存在且非空
    - 将解析后的数据存入 request.json_data

    使用示例:
        @app.route('/create', methods=['POST'])
        @validate_json_request('user_id', 'work_id')
        def create():
            data = request.json_data  # 已验证的数据
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if data is None:
                return error_response("Request body must be JSON", 400)

            missing = [field for field in required_fields if field not in data or not data[field]]
            if missing:
                return error_response(f"Missing required fields: {', '.join(missing)}", 400)

            request.json_data = data
            return f(*args, **kwargs)
        return decorated
    return decorator


def log_api_call(f):
    """
    记录 API 调用的装饰器

    功能:
    - 记录请求方法、路径、参数
    - 记录响应状态码
    - 可选记录请求耗时
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        import time
        start_time = time.time()
        logger = logging.getLogger(__name__)

        log_data = {
            'method': request.method,
            'path': request.path,
            'args': request.args.to_dict() if request.args else None,
        }
        logger.info(f"API call started: {log_data}")

        result = f(*args, **kwargs)

        elapsed = time.time() - start_time
        status_code = result[1] if isinstance(result, tuple) else 200
        logger.info(f"API call completed: status={status_code}, elapsed={elapsed:.3f}s")
        return result
    return decorated


def audit_log(action_name: str):
    """
    审计日志装饰器 - 用于记录关键操作

    参数:
        action_name: 操作名称 (如 'CREATE_SHOT', 'DELETE_ASSET')

    功能:
    - 记录用户 ID (从 JWT 获取)
    - 记录操作类型和时间
    - 记录请求参数

    使用示例:
        @shots_bp.route('/createShot', methods=['POST'])
        @audit_log('CREATE_SHOT')
        def create_shot():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            logger = logging.getLogger('audit')
            import json

            user_id = g.current_user_id if hasattr(g, 'current_user_id') else 'anonymous'

            # 获取请求数据
            try:
                request_data = request.get_json() or request.form.to_dict()
            except:
                request_data = None

            logger.info(
                f"Audit: {action_name}",
                extra={
                    'user_id': user_id,
                    'action': action_name,
                    'method': request.method,
                    'path': request.path,
                    'request_data': json.dumps(request_data) if request_data else None
                }
            )

            return f(*args, **kwargs)
        return decorated
    return decorator


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


def jwt_required(f):
    """
    JWT 认证装饰器
    验证请求头中的 Bearer Token

    使用方式:
        @user_bp.route('/protected')
        @jwt_required
        def protected_route():
            user_id = g.current_user_id  # 从 g 对象获取用户 ID
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 从 Authorization 头获取 token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                elif auth_header.startswith('Bearer'):
                    # Bearer 后面没有空格的情况
                    token = auth_header[6:].strip()
            except IndexError:
                return error_response('Invalid bearer token format', 401)

        if not token:
            return error_response('Authentication token required', 401)

        # 验证 token
        try:
            from services.jwt_service import jwt_service
            from services.token_blacklist_service import token_blacklist_service

            # 先解码获取 JTI
            payload = jwt_service.decode_token(token)

            # 检查黑名单（仅针对 access token）
            if payload.get('type') == 'access':
                jti = payload.get('jti', '')
                if token_blacklist_service.is_blacklisted(jti):
                    return error_response('Token has been revoked', 401)

            # 验证 token
            verified_payload = jwt_service.verify_access_token(token)

            # 将用户信息存入 g 对象供路由使用
            g.current_user_id = verified_payload['user_id']
            g.current_user_email = verified_payload.get('email')
            g.current_token_payload = verified_payload
            g.current_token = token

        except jwt.ExpiredSignatureError:
            return error_response('Token has expired', 401)
        except jwt.InvalidTokenError as e:
            return error_response(f'Invalid token: {str(e)}', 401)
        except Exception as e:
            logging.error(f"JWT verification error: {e}")
            return error_response('Token verification failed', 401)

        return f(*args, **kwargs)
    return decorated


def optional_jwt(f):
    """
    可选 JWT 认证装饰器
    如果有 token 则验证，没有也不报错

    使用方式:
        @user_bp.route('/public-or-private')
        @optional_jwt
        def public_or_private_route():
            if g.current_user_id:
                # 用户已登录
                ...
            else:
                # 游客访问
                ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if token:
            try:
                from services.jwt_service import jwt_service
                from services.token_blacklist_service import token_blacklist_service

                payload = jwt_service.decode_token(token)

                # 检查黑名单
                if payload.get('type') == 'access':
                    jti = payload.get('jti', '')
                    if not token_blacklist_service.is_blacklisted(jti):
                        verified_payload = jwt_service.verify_access_token(token)
                        g.current_user_id = verified_payload['user_id']
                        g.current_user_email = verified_payload.get('email')
                        g.current_token_payload = verified_payload
                        g.current_token = token

            except:
                pass  # Token 无效但继续请求，作为游客处理

        return f(*args, **kwargs)
    return decorated
