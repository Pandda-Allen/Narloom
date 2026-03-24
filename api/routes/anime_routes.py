# api/routes/anime_routes.py
"""
Anime Routes 模块
提供漫画图片动画生成等功能
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors
from utils.general_helper import validate_required_fields
from utils.constants import (
    RequestParams, ResponseMessage, Defaults, FileTypes, SessionConfig,
)
from services.anime_service import anime_service
from services.video_generation_service import video_generation_service
from services.conversation_history import conversation_history
from services.mysql_service import MySQLService
from services.mongo_service import MongoService
from services.picture_service import picture_service
import logging
import uuid

anime_bp = Blueprint('anime', __name__)
logger = logging.getLogger(__name__)


def _get_picture_source(user_id: str, asset_id: str = None, oss_object_key: str = None):
    """
    获取图片来源的辅助函数

    优先级：
    1. 如果提供了 asset_id，从数据库获取图片 URL
    2. 如果提供了 oss_object_key，直接生成 URL
    3. 如果都没有，返回 None

    Args:
        user_id: 用户 ID
        asset_id: 资产 ID（可选）
        oss_object_key: OSS 对象键（可选）

    Returns:
        tuple: (picture_url, oss_object_key)
    """
    # 1. 如果提供了 asset_id，从数据库获取
    if asset_id:
        mysql_row = MySQLService().fetch_asset_by_id(asset_id)
        if mysql_row and mysql_row['user_id'] == user_id:
            asset_data = MongoService().fetch_asset_data(asset_id)
            if asset_data:
                return asset_data.get('oss_url'), asset_data.get('oss_object_key')

    # 2. 如果提供了 oss_object_key，直接使用
    if oss_object_key:
        url_result = picture_service.get_picture_url(oss_object_key)
        if url_result.get('success'):
            return url_result['url'], oss_object_key

    return None, None


def _get_picture_from_request(user_id: str):
    """
    从请求中获取上传的图片文件并上传到 OSS

    Args:
        user_id: 用户 ID

    Returns:
        tuple: (picture_url, oss_object_key) 或 (None, None)
    """
    if RequestParams.PICTURE in request.files:
        file = request.files[RequestParams.PICTURE]
        if file and file.filename:
            file_content = file.read()
            file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else Defaults.IMAGE_EXTENSION
            object_key = picture_service.generate_object_key(user_id, file_extension)

            upload_result = picture_service.upload_picture(
                file_content=file_content,
                object_key=object_key,
                content_type=file.content_type or FileTypes.IMAGE_JPEG
            )

            if upload_result.get('success'):
                return upload_result['url'], object_key

    return None, None


@anime_bp.route('/generateAnime', methods=['POST'])
@handle_errors
def generate_anime():
    """
    生成动画（图生视频）- 主入口函数

    请求参数：
    - user_id: 用户 ID (必填)
    - session_id: 会话 ID (可选，用于多轮对话)
    - asset_id: 已上传图片的资产 ID (可选)
    - oss_object_key: OSS 对象键 (可选)
    - picture: 新图片文件 (可选)
    - parameters: 生成参数 (可选)

    返回：
    - session_id: 会话 ID
    - video_url: 生成的视频 URL
    - preview_url: 预览图 URL
    """
    # 解析请求数据
    data = request.form if request.files else request.get_json() or {}
    if data is None:
        return error_response(ResponseMessage.INVALID_REQUEST, 400)

    validate_required_fields(data, [RequestParams.USER_ID])

    # 提取参数
    user_id = data.get(RequestParams.USER_ID)
    session_id = data.get(RequestParams.SESSION_ID)
    asset_id = data.get(RequestParams.ASSET_ID)
    oss_object_key = data.get(RequestParams.OSS_OBJECT_KEY)
    parameters = data.get(RequestParams.PARAMETERS, {})

    # 获取图片 URL
    picture_url, oss_object_key = _get_picture_source(user_id, asset_id, oss_object_key)

    # 如果没有找到图片，尝试从请求文件中获取
    if not picture_url:
        picture_url, oss_object_key = _get_picture_from_request(user_id)

    if not picture_url:
        return error_response('Must provide either picture file, asset_id, or oss_object_key', 400)

    # 如果没有 session_id，创建新会话
    if not session_id:
        session_id = str(uuid.uuid4())
        conversation_history.create_session(
            session_id=session_id,
            user_id=user_id,
            context_type=SessionConfig.CONTEXT_TYPE_ANIME_GENERATION,
            context_data={
                RequestParams.ASSET_ID: asset_id,
                RequestParams.OSS_OBJECT_KEY: oss_object_key,
                'image_url': picture_url
            }
        )

    # 调用生成服务
    result = anime_service.generate_anime(
        session_id, user_id, picture_url, oss_object_key, parameters,
        conversation_history, video_generation_service
    )

    if result.get('success'):
        return api_response(
            success=True,
            message=ResponseMessage.GENERATE_SUCCESS,
            data=result,
            count=1
        )
    else:
        return error_response(result.get('error'), 500)


@anime_bp.route('/chat', methods=['POST'])
@handle_errors
def chat():
    """
    多轮对话交互入口

    请求参数：
    - user_id: 用户 ID (必填)
    - session_id: 会话 ID (可选，用于多轮对话)
    - asset_id: 已上传图片的资产 ID (可选)
    - oss_object_key: OSS 对象键 (可选)
    - picture: 新图片文件 (可选)
    - message: 用户消息 (必填)

    返回：
    - session_id: 会话 ID
    - response: AI 回复内容
    - summary: 对话总结
    - turn_count: 对话轮数
    """
    # 解析请求数据
    data = request.form if request.files else request.get_json() or {}
    if data is None:
        return error_response(ResponseMessage.INVALID_REQUEST, 400)

    validate_required_fields(data, [RequestParams.USER_ID, RequestParams.MESSAGE])

    # 提取参数
    user_id = data.get(RequestParams.USER_ID)
    session_id = data.get(RequestParams.SESSION_ID) or str(uuid.uuid4())
    user_message = data.get(RequestParams.MESSAGE)
    asset_id = data.get(RequestParams.ASSET_ID)
    oss_object_key = data.get(RequestParams.OSS_OBJECT_KEY)

    # 获取图片 URL
    picture_url, oss_object_key = _get_picture_source(user_id, asset_id, oss_object_key)

    # 如果没有找到图片，尝试从请求文件中获取
    if not picture_url:
        picture_url, oss_object_key = _get_picture_from_request(user_id)

    # 调用聊天服务
    result = anime_service.chat(
        session_id, user_id, picture_url, oss_object_key, user_message,
        conversation_history
    )

    if result.get('success'):
        return api_response(
            success=True,
            message=ResponseMessage.CHAT_SUCCESS,
            data=result,
            count=1
        )
    else:
        return error_response(result.get('error'), 400)


@anime_bp.route('/confirm', methods=['POST'])
@handle_errors
def confirm():
    """
    确认保存生成的视频

    请求参数：
    - user_id: 用户 ID (必填)
    - video_url: 视频 URL (必填)
    - preview_url: 预览图 URL (可选)
    - parameters: 其他参数 (可选)

    返回：
    - asset_id: 创建的资产 ID
    - video_url: 视频 URL
    - preview_url: 预览图 URL
    """
    # 解析请求数据
    data = request.get_json() or {}
    if data is None:
        return error_response('Request body must be JSON', 400)

    validate_required_fields(data, [RequestParams.USER_ID, RequestParams.VIDEO_URL])

    # 提取参数
    user_id = data.get(RequestParams.USER_ID)
    parameters = data.get(RequestParams.PARAMETERS, {})

    # 调用确认服务
    result = anime_service.confirm(user_id, parameters, conversation_history)

    if result.get('success'):
        return api_response(
            success=True,
            message=ResponseMessage.CONFIRM_SUCCESS,
            data=result,
            count=1
        )
    else:
        return error_response(result.get('error'), 500)


@anime_bp.route('/health', methods=['GET'])
@handle_errors
def health_check():
    """健康检查"""
    return api_response(
        success=True,
        message=ResponseMessage.HEALTH_CHECK_SUCCESS,
        data={
            'service': 'anime'
        }
    )
