# api/routes/anime.py
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
from services.db import MySQLService, MongoService
from services.storage import oss_service
import logging
import uuid
from typing import List, Dict

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
        url_result = oss_service.get_picture_url(oss_object_key)
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
            object_key = oss_service.generate_object_key(user_id, file_extension)

            upload_result = oss_service.upload_picture(
                file_content=file_content,
                object_key=object_key,
                content_type=file.content_type or FileTypes.IMAGE_JPEG
            )

            if upload_result.get('success'):
                return upload_result['url'], object_key

    return None, None


def _get_pictures_from_request(user_id: str) -> List[Dict]:
    """
    从请求中获取上传的多张图片文件并上传到 OSS

    Args:
        user_id: 用户 ID

    Returns:
        List[Dict]: 图片列表，每个元素包含 {'picture_url': str, 'oss_object_key': str}
    """
    images = []

    # 支持多文件上传 (pictures) 或单个文件 (picture)
    files = request.files.getlist('pictures')
    if not files:
        # 尝试从 picture 字段获取
        if RequestParams.PICTURE in request.files:
            files = request.files.getlist(RequestParams.PICTURE)

    for file in files:
        if file and file.filename:
            file_content = file.read()
            file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else Defaults.IMAGE_EXTENSION
            object_key = oss_service.generate_object_key(user_id, file_extension)

            upload_result = oss_service.upload_picture(
                file_content=file_content,
                object_key=object_key,
                content_type=file.content_type or FileTypes.IMAGE_JPEG
            )

            if upload_result.get('success'):
                images.append({
                    'picture_url': upload_result['url'],
                    'oss_object_key': object_key,
                    'original_filename': file.filename
                })

    return images


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


@anime_bp.route('/generateMultiImageAnime', methods=['POST'])
@handle_errors
def generate_multi_image_anime():
    """
    为多张图片依次生成动画并合并成一个视频

    请求参数：
    - user_id: 用户 ID (必填)
    - session_id: 会话 ID (可选，用于多轮对话)
    - pictures: 多张图片文件 (multipart/form-data，至少 1 张)
    - asset_ids: 已上传图片的资产 ID 列表 (可选，逗号分隔)
    - oss_object_keys: OSS 对象键列表 (可选，逗号分隔)
    - parameters: 生成参数 (可选)
        - prompt: 提示词
        - style: 风格 (默认 anime)
        - duration: 每张图片的动画时长 (默认 5 秒)
        - motion_strength: 运动强度 (默认 0.5)
        - transition: 转场效果 (默认 fade)
        - transition_duration: 转场时长 (默认 0.5 秒)

    返回：
    - session_id: 会话 ID
    - video_url: 合并后的视频 URL
    - preview_url: 预览图 URL
    - panel_count: 图片数量
    - total_duration: 总时长
    - individual_videos: 每个图片生成的视频详情
    """
    # 解析请求数据
    data = request.form if request.files else request.get_json() or {}
    if data is None:
        return error_response(ResponseMessage.INVALID_REQUEST, 400)

    validate_required_fields(data, [RequestParams.USER_ID])

    # 提取参数
    user_id = data.get(RequestParams.USER_ID)
    session_id = data.get(RequestParams.SESSION_ID)
    parameters = data.get(RequestParams.PARAMETERS, {})

    # 获取图片列表
    images = []

    # 1. 从 asset_ids 获取图片
    asset_ids_str = data.get('asset_ids', '')
    if asset_ids_str:
        asset_ids = [aid.strip() for aid in asset_ids_str.split(',') if aid.strip()]
        for asset_id in asset_ids:
            mysql_row = MySQLService().fetch_asset_by_id(asset_id)
            if mysql_row and mysql_row['user_id'] == user_id:
                asset_data = MongoService().fetch_asset_data(asset_id)
                if asset_data:
                    images.append({
                        'picture_url': asset_data.get('oss_url'),
                        'oss_object_key': asset_data.get('oss_object_key')
                    })

    # 2. 从 oss_object_keys 获取图片
    oss_object_keys_str = data.get('oss_object_keys', '')
    if oss_object_keys_str:
        oss_object_keys = [key.strip() for key in oss_object_keys_str.split(',') if key.strip()]
        for oss_object_key in oss_object_keys:
            url_result = oss_service.get_picture_url(oss_object_key)
            if url_result.get('success'):
                images.append({
                    'picture_url': url_result['url'],
                    'oss_object_key': oss_object_key
                })

    # 3. 从上传的文件获取图片
    uploaded_images = _get_pictures_from_request(user_id)
    images.extend(uploaded_images)

    # 验证至少有一张图片
    if not images:
        return error_response('Must provide at least one image via pictures, asset_ids, or oss_object_keys', 400)

    # 创建会话
    if not session_id:
        session_id = str(uuid.uuid4())

    # 调用生成服务
    result = anime_service.generate_multi_image_anime(
        session_id, user_id, images, parameters,
        conversation_history, video_generation_service
    )

    if result.get('success'):
        return api_response(
            success=True,
            message=ResponseMessage.GENERATE_SUCCESS,
            data=result,
            count=len(images)
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
