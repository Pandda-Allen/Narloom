# api/routes/shots.py
"""
Shots Routes 模块
提供镜头（shot）管理和动画生成等功能
用于 anime 类型的作品，每个 work 由多个 shots 组成
每个 shot 包含多个 asset（anime 视频 + 上传的 picture）
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors
from utils.general_helper import validate_required_fields
from utils.constants import RequestParams, ResponseMessage, Defaults, FileTypes
from services.db import MySQLService, MongoService
from services.storage import oss_service
import logging
import uuid
from typing import List, Dict

shots_bp = Blueprint('shots', __name__)
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


def _get_picture_from_request(user_id: str, field_name: str = RequestParams.PICTURE,
                               work_id: str = None, shot_id: str = None):
    """
    从请求中获取上传的图片文件并上传到 OSS

    Args:
        user_id: 用户 ID
        field_name: 表单字段名 (默认 'picture'，尾帧可用 'end_picture')
        work_id: 作品 ID (可选，用于关联作品)
        shot_id: 镜头 ID (可选，用于关联镜头)

    Returns:
        tuple: (picture_url, oss_object_key, asset_id) 或 (None, None, None)
    """
    if field_name in request.files:
        file = request.files[field_name]
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
                # 如果需要关联 work/shot，创建资产记录
                asset_id = None
                if work_id:
                    asset_record = MySQLService().insert_asset(user_id, 'picture', work_id)
                    asset_id = asset_record['asset_id']
                    # 保存 OSS 信息到 MongoDB
                    from datetime import datetime
                    asset_data = {
                        'type': 'picture',
                        'oss_url': upload_result['url'],
                        'oss_object_key': object_key,
                        'original_filename': file.filename,
                        'shot_id': shot_id,
                        'created_at': datetime.now().isoformat()
                    }
                    MongoService().insert_asset_data(asset_id, asset_data)

                return upload_result['url'], object_key, asset_id

    return None, None, None


def _get_pictures_from_request(user_id: str, work_id: str = None,
                                shot_id: str = None) -> List[Dict]:
    """
    从请求中获取上传的多张图片文件并上传到 OSS

    Args:
        user_id: 用户 ID
        work_id: 作品 ID (可选，用于关联作品)
        shot_id: 镜头 ID (可选，用于关联镜头)

    Returns:
        List[Dict]: 图片列表，每个元素包含 {'picture_url': str, 'oss_object_key': str, 'asset_id': str}
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
                # 如果需要关联 work/shot，创建资产记录
                asset_id = None
                if work_id:
                    asset_record = MySQLService().insert_asset(user_id, 'picture', work_id)
                    asset_id = asset_record['asset_id']
                    # 保存 OSS 信息到 MongoDB
                    from datetime import datetime
                    asset_data = {
                        'type': 'picture',
                        'oss_url': upload_result['url'],
                        'oss_object_key': object_key,
                        'original_filename': file.filename,
                        'shot_id': shot_id,
                        'created_at': datetime.now().isoformat()
                    }
                    MongoService().insert_asset_data(asset_id, asset_data)

                images.append({
                    'picture_url': upload_result['url'],
                    'oss_object_key': object_key,
                    'original_filename': file.filename,
                    'asset_id': asset_id
                })

    return images


@shots_bp.route('/createShot', methods=['POST'])
@handle_errors
def create_shot():
    """
    创建新的镜头（shot）

    请求参数：
    - work_id: 作品 ID (必填)
    - author_id: 作者 ID (必填)
    - shot_number: 镜头编号 (必填)
    - description: 镜头描述 (可选)
    - notes: 备注 (可选)

    返回：
    - shot_id: 镜头 ID
    - work_id: 作品 ID
    - shot_number: 镜头编号
    """
    data = request.get_json() or {}
    validate_required_fields(data, ['work_id', 'author_id', 'shot_number'])

    work_id = data.get('work_id')
    author_id = data.get('author_id')
    shot_number = data.get('shot_number')
    description = data.get('description', '')
    notes = data.get('notes', '')

    # 插入 MySQL shots
    shot = MySQLService().insert_shot(
        work_id=work_id,
        author_id=author_id,
        shot_number=shot_number,
        description=description,
        notes=notes
    )
    shot_id = shot['shot_id']

    # 更新 MongoDB anime_details
    try:
        MongoService().add_shot_to_anime(work_id, shot_id)
    except Exception as e:
        logger.error(f"Error updating anime details: {str(e)}")
        # 回滚：删除 MySQL 中的镜头
        MySQLService().delete_shot(shot_id)
        return error_response('Failed to update anime details', 500)

    # 初始化 shot_details
    try:
        MongoService().insert_shot_details(
            shot_id=shot_id,
            work_id=work_id,
            asset_ids=[],
            video_assets=[],
            picture_assets=[]
        )
    except Exception as e:
        logger.error(f"Error creating shot details: {str(e)}")
        # 回滚
        MySQLService().delete_shot(shot_id)
        MongoService().remove_shot_from_anime(work_id, shot_id)
        return error_response('Failed to create shot details', 500)

    return api_response(
        success=True,
        message='Shot created successfully',
        data=shot,
        count=1
    )


@shots_bp.route('/getShotsByWorkId', methods=['GET'])
@handle_errors
def get_shots_by_work_id():
    """
    根据作品 ID 获取镜头列表

    请求参数：
    - work_id: 作品 ID (必填)

    返回：
    - shots: 镜头列表
    """
    validate_required_fields(request.args, ['work_id'])
    work_id = request.args.get('work_id')

    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return error_response('Invalid pagination parameters', 400)

    shots = MySQLService().fetch_shots_by_work_id(work_id, limit, offset)
    return api_response(
        success=True,
        message='Shots fetched successfully',
        data=shots,
        count=len(shots)
    )


@shots_bp.route('/generateAnime', methods=['POST'])
@handle_errors
def generate_anime():
    """
    为指定镜头生成动画（图生视频）

    请求参数：
    - user_id: 用户 ID (必填)
    - work_id: 作品 ID (必填)
    - shot_id: 镜头 ID (必填)
    - session_id: 会话 ID (可选，用于多轮对话)
    - frame_mode: 帧模式 (可选，single / start_end，默认 single)
    - 首帧图片参数 (三选一):
        - asset_id: 已上传图片的资产 ID
        - oss_object_key: OSS 对象键
        - picture: 新图片文件
    - 尾帧图片参数 (frame_mode=start_end 时必填，三选一):
        - end_asset_id: 已上传图片的资产 ID
        - end_oss_object_key: OSS 对象键
        - end_picture: 新图片文件
    - parameters: 生成参数 (可选)
        - prompt: 提示词
        - style: 风格 (默认 anime)
        - duration: 动画时长 (默认 5 秒)
        - motion_strength: 运动强度 (默认 0.5)

    返回：
    - session_id: 会话 ID
    - video_url: 生成的视频 URL
    - shot_id: 镜头 ID
    - asset_id: 生成的视频资产 ID
    - frame_mode: 使用的帧模式
    """
    # 解析请求数据
    data = request.form if request.files else request.get_json() or {}
    if data is None:
        return error_response(ResponseMessage.INVALID_REQUEST, 400)

    validate_required_fields(data, [RequestParams.USER_ID, RequestParams.WORK_ID, 'shot_id'])

    # 提取参数
    user_id = data.get(RequestParams.USER_ID)
    work_id = data.get(RequestParams.WORK_ID)
    shot_id = data.get('shot_id')
    session_id = data.get(RequestParams.SESSION_ID)
    frame_mode = data.get('frame_mode', 'single')

    # 首帧图片参数
    asset_id = data.get(RequestParams.ASSET_ID)
    oss_object_key = data.get(RequestParams.OSS_OBJECT_KEY)

    # 尾帧图片参数
    end_asset_id = data.get('end_asset_id')
    end_oss_object_key = data.get('end_oss_object_key')

    parameters = data.get(RequestParams.PARAMETERS, {})

    # 获取首帧图片 URL（优先级：asset_id -> oss_object_key -> picture 文件）
    picture_url, picture_oss_key = _get_picture_source(user_id, asset_id, oss_object_key)
    if not picture_url:
        picture_url, picture_oss_key, _ = _get_picture_from_request(
            user_id, RequestParams.PICTURE, work_id, shot_id)

    if not picture_url:
        return error_response('Must provide picture file, asset_id, or oss_object_key for start frame', 400)

    # 获取尾帧图片 URL (如果需要)
    end_picture_url = None
    end_picture_oss_key = None
    if frame_mode == 'start_end':
        end_picture_url, end_picture_oss_key = _get_picture_source(
            user_id, end_asset_id, end_oss_object_key)
        if not end_picture_url:
            end_picture_url, end_picture_oss_key, _ = _get_picture_from_request(
                user_id, 'end_picture', work_id, shot_id)

        if not end_picture_url:
            return error_response(
                'Must provide end_picture file, end_asset_id, or end_oss_object_key when frame_mode=start_end', 400)

    # 调用 anime 服务生成动画
    from services.anime_service import anime_service

    # 临时传递 shot_id 到 parameters
    parameters['_shot_id'] = shot_id
    parameters['_work_id'] = work_id

    result = anime_service.generate_anime(
        session_id=session_id,
        user_id=user_id,
        first_frame_url=picture_url,
        first_frame_oss_key=picture_oss_key,
        last_frame_url=end_picture_url,
        last_frame_oss_key=end_picture_oss_key,
        parameters=parameters,
        work_id=work_id,
        shot_id=shot_id
    )

    if result.get('success'):
        # 保存生成的视频到 shot_details
        if result.get('asset_id'):
            MongoService().add_asset_to_shot(
                shot_id=shot_id,
                asset_id=result.get('asset_id'),
                asset_type='video',
                asset_data={
                    'asset_id': result.get('asset_id'),
                    'video_url': result.get('video_url'),
                    'frame_mode': result.get('frame_mode'),
                    'created_at': result.get('created_at')
                }
            )

        return api_response(
            success=True,
            message=ResponseMessage.GENERATE_SUCCESS,
            data=result,
            count=1
        )
    else:
        return error_response(result.get('error'), 500)


@shots_bp.route('/generateMultiImageAnime', methods=['POST'])
@handle_errors
def generate_multi_image_anime():
    """
    为多张图片依次生成动画并合并成一个视频

    请求参数：
    - user_id: 用户 ID (必填)
    - work_id: 作品 ID (必填)
    - shot_id: 镜头 ID (必填)
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
        - frame_mode: 帧模式 (可选，single / start_end)

    返回：
    - session_id: 会话 ID
    - video_url: 合并后的视频 URL
    - shot_id: 镜头 ID
    - asset_id: 生成的视频资产 ID
    - panel_count: 图片数量
    - total_duration: 总时长
    """
    # 解析请求数据
    data = request.form if request.files else request.get_json() or {}
    if data is None:
        return error_response(ResponseMessage.INVALID_REQUEST, 400)

    validate_required_fields(data, [RequestParams.USER_ID, RequestParams.WORK_ID, 'shot_id'])

    # 提取参数
    user_id = data.get(RequestParams.USER_ID)
    work_id = data.get(RequestParams.WORK_ID)
    shot_id = data.get('shot_id')
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
                        'oss_object_key': asset_data.get('oss_object_key'),
                        'asset_id': asset_id
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
    uploaded_images = _get_pictures_from_request(user_id, work_id, shot_id)
    images.extend(uploaded_images)

    # 验证至少有一张图片
    if not images:
        return error_response('Must provide at least one image via pictures, asset_ids, or oss_object_keys', 400)

    # 创建会话
    if not session_id:
        session_id = str(uuid.uuid4())

    # 调用生成服务
    from services.anime_service import anime_service

    # 临时传递 shot_id 到 parameters
    parameters['_shot_id'] = shot_id
    parameters['_work_id'] = work_id

    result = anime_service.generate_multi_image_anime(
        session_id=session_id,
        user_id=user_id,
        images=images,
        parameters=parameters,
        work_id=work_id,
        shot_id=shot_id
    )

    if result.get('success'):
        # 保存生成的视频到 shot_details
        if result.get('asset_id'):
            MongoService().add_asset_to_shot(
                shot_id=shot_id,
                asset_id=result.get('asset_id'),
                asset_type='video',
                asset_data={
                    'asset_id': result.get('asset_id'),
                    'video_url': result.get('video_url'),
                    'frame_mode': result.get('frame_mode'),
                    'created_at': result.get('created_at')
                }
            )

        return api_response(
            success=True,
            message=ResponseMessage.GENERATE_SUCCESS,
            data=result,
            count=len(images)
        )
    else:
        return error_response(result.get('error'), 500)


@shots_bp.route('/confirm', methods=['POST'])
@handle_errors
def confirm():
    """
    确认保存生成的视频到 shot_details

    请求参数：
    - user_id: 用户 ID (必填)
    - work_id: 作品 ID (必填)
    - shot_id: 镜头 ID (必填)
    - video_url: 视频 URL (必填)
    - preview_url: 预览图 URL (可选)
    - parameters: 其他参数 (可选)

    返回：
    - asset_id: 创建的资产 ID
    - video_url: 视频 URL
    - shot_id: 镜头 ID
    """
    # 解析请求数据
    data = request.get_json() or {}
    if data is None:
        return error_response('Request body must be JSON', 400)

    validate_required_fields(data, [RequestParams.USER_ID, RequestParams.WORK_ID, 'shot_id', RequestParams.VIDEO_URL])

    # 提取参数
    user_id = data.get(RequestParams.USER_ID)
    work_id = data.get(RequestParams.WORK_ID)
    shot_id = data.get('shot_id')
    parameters = data.get(RequestParams.PARAMETERS, {})

    # 调用确认服务
    from services.anime_service import anime_service
    result = anime_service.confirm(user_id=user_id, work_id=work_id, shot_id=shot_id, parameters=parameters)

    if result.get('success'):
        # 添加到 shot_details
        MongoService().add_asset_to_shot(
            shot_id=shot_id,
            asset_id=result.get('asset_id'),
            asset_type='video',
            asset_data={
                'asset_id': result.get('asset_id'),
                'video_url': result.get('video_url'),
                'oss_object_key': result.get('oss_object_key'),
                'created_at': result.get('created_at')
            }
        )

        return api_response(
            success=True,
            message=ResponseMessage.CONFIRM_SUCCESS,
            data=result,
            count=1
        )
    else:
        return error_response(result.get('error'), 500)


@shots_bp.route('/getShotDetails', methods=['GET'])
@handle_errors
def get_shot_details():
    """
    获取镜头详情（包含所有 asset）

    请求参数：
    - shot_id: 镜头 ID (必填)

    返回：
    - shot_id: 镜头 ID
    - work_id: 作品 ID
    - asset_ids: 资产 ID 列表
    - video_assets: 视频资产列表
    - picture_assets: 图片资产列表
    """
    validate_required_fields(request.args, ['shot_id'])
    shot_id = request.args.get('shot_id')

    shot_details = MongoService().fetch_shot_details(shot_id)
    shot_info = MySQLService().fetch_shot_by_id(shot_id)

    if shot_info:
        shot_details = shot_details or {}
        shot_details.update(shot_info)

    return api_response(
        success=True,
        message='Shot details fetched successfully',
        data=shot_details or {},
        count=1 if shot_details else 0
    )


@shots_bp.route('/health', methods=['GET'])
@handle_errors
def health_check():
    """健康检查"""
    return api_response(
        success=True,
        message=ResponseMessage.HEALTH_CHECK_SUCCESS,
        data={
            'service': 'shots'
        }
    )
