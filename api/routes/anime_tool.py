# api/routes/anime_tool.py
"""
Anime Tool 路由模块
提供漫画图片上传、获取、生成视频、删除等功能
"""
from flask import Blueprint, request, current_app
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors
from utils.general_helper import validate_required_fields
from services.anime_tool_service import anime_tool_service
from services.mysql_service import MySQLService
from services.mongo_service import MongoService
import logging
import uuid
from datetime import datetime

anime_tool_bp = Blueprint('anime-tool', __name__)
logger = logging.getLogger(__name__)


@anime_tool_bp.route('/uploadPicture', methods=['POST'])
@handle_errors
def upload_picture():
    """
    上传漫画图片到阿里云 OSS

    请求参数：
    - picture: 图片文件 (multipart/form-data)
    - user_id: 用户 ID (必填)
    - work_id: 作品 ID (可选，关联到特定作品)

    返回：
    - asset_id: 创建的资产 ID
    - url: 图片访问 URL
    - object_key: OSS 中的对象键
    """
    # 检查是否有文件上传
    if 'picture' not in request.files:
        return error_response('No picture file provided', 400)

    file = request.files['picture']
    if file.filename == '':
        return error_response('No file selected', 400)

    # 获取表单数据
    data = request.form
    validate_required_fields(data, ['user_id'])

    user_id = data.get('user_id')
    work_id = data.get('work_id', None)

    # 读取文件内容
    file_content = file.read()
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'

    # 生成 OSS 对象键
    object_key = anime_tool_service.generate_object_key(user_id, file_extension)

    # 上传到 OSS
    upload_result = anime_tool_service.upload_picture(
        file_content=file_content,
        object_key=object_key,
        content_type=file.content_type or 'image/jpeg'
    )

    if not upload_result.get('success'):
        return error_response(f"Failed to upload picture: {upload_result.get('error')}", 500)

    # 创建 asset 记录（类型：comic）
    mysql_row = MySQLService().insert_asset(user_id, 'comic', work_id)
    asset_id = mysql_row['asset_id']

    # 创建 asset_data 记录
    asset_data = {
        'type': 'comic_picture',
        'oss_url': upload_result['url'],
        'oss_object_key': object_key,
        'original_filename': file.filename,
        'file_size': len(file_content),
        'upload_timestamp': datetime.now().isoformat()
    }

    try:
        MongoService().insert_asset_data(asset_id, asset_data)
    except Exception as e:
        logger.error(f"Error inserting asset data to MongoDB: {str(e)}")
        # 回滚：删除 MySQL 和 OSS 中的数据
        MySQLService().delete_asset(asset_id)
        anime_tool_service.delete_picture(object_key)
        return error_response('Failed to create asset record', 500)

    result = {
        'asset_id': asset_id,
        'user_id': user_id,
        'work_id': work_id,
        'url': upload_result['url'],
        'object_key': object_key,
        'original_filename': file.filename,
        'file_size': len(file_content)
    }

    return api_response(
        success=True,
        message='Picture uploaded successfully',
        data=result,
        count=1
    )


@anime_tool_bp.route('/fetchPicture', methods=['GET'])
@handle_errors
def fetch_picture():
    """
    获取用户已上传的漫画图片列表

    请求参数：
    - user_id: 用户 ID (必填)
    - work_id: 作品 ID (可选，筛选特定作品的图片)
    - limit: 返回数量限制 (可选，默认 100)
    - offset: 偏移量 (可选，默认 0)
    - oss_list: 是否从 OSS 直接获取列表 (可选，默认 false，设为 true 时直接从 OSS 获取)

    返回：
    - pictures: 图片列表
    """
    validate_required_fields(request.args, ['user_id'])

    user_id = request.args.get('user_id')
    work_id = request.args.get('work_id', None)
    oss_list = request.args.get('oss_list', 'false').lower() == 'true'

    # 如果直接从 OSS 获取
    if oss_list:
        prefix = f"comic/{user_id}/"
        limit_str = request.args.get('limit', '100')
        marker = request.args.get('marker', '')

        try:
            limit = int(limit_str)
        except ValueError:
            return error_response('limit must be an integer', 400)

        oss_result = anime_tool_service.list_pictures(prefix=prefix, max_keys=limit, marker=marker)

        if not oss_result.get('success'):
            return error_response(f"Failed to fetch pictures: {oss_result.get('error')}", 500)

        return api_response(
            success=True,
            message='Pictures fetched successfully from OSS',
            data={
                'pictures': oss_result['pictures'],
                'is_truncated': oss_result['is_truncated'],
                'next_marker': oss_result['next_marker']
            },
            count=oss_result['count']
        )

    # 从数据库获取（默认方式）
    try:
        # 解析分页参数
        limit_str = request.args.get('limit', '100')
        offset_str = request.args.get('offset', '0')
        limit = int(limit_str)
        offset = int(offset_str)
    except ValueError:
        return error_response('limit and offset must be integers', 400)

    # 从 MySQL 获取资产列表
    mysql_rows = MySQLService().fetch_assets(user_id, asset_type='comic', work_id=work_id, limit=limit, offset=offset)

    if not mysql_rows:
        return api_response(
            success=True,
            message='No pictures found',
            data=[],
            count=0
        )

    # 获取 MongoDB 中的 asset_data
    asset_ids = [row['asset_id'] for row in mysql_rows]
    asset_data_map = MongoService().fetch_multiple_asset_data(asset_ids)

    # 构建返回结果
    results = []
    for row in mysql_rows:
        asset_data = asset_data_map.get(row['asset_id'], {})
        results.append({
            'asset_id': row['asset_id'],
            'user_id': row['user_id'],
            'work_id': row.get('work_id'),
            'url': asset_data.get('oss_url', ''),
            'object_key': asset_data.get('oss_object_key', ''),
            'original_filename': asset_data.get('original_filename', ''),
            'file_size': asset_data.get('file_size', 0),
            'upload_timestamp': asset_data.get('upload_timestamp', ''),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        })

    return api_response(
        success=True,
        message='Pictures fetched successfully',
        data=results,
        count=len(results)
    )


@anime_tool_bp.route('/generateAnime', methods=['POST'])
@handle_errors
def generate_anime():
    """
    生成动画（图生视频）- 框架接口

    请求参数：
    - user_id: 用户 ID (必填)
    - asset_id: 已上传图片的资产 ID (可选，选中已有图片时使用)
    - oss_object_key: OSS 对象键 (可选，直接指定 OSS 中的图片)
    - picture: 新图片文件 (可选，上传新图片时使用 multipart/form-data)
    - parameters: 生成参数 (可选)
        - duration: 视频时长（秒）
        - fps: 帧率
        - style: 风格类型
        - motion_strength: 运动强度
        - prompt: 生成提示词

    返回：
    - task_id: 生成任务 ID
    - status: 任务状态
    """
    data = request.form if request.files else request.get_json() or {}

    if data is None:
        return error_response('Request body must be JSON or multipart/form-data', 400)

    validate_required_fields(data, ['user_id'])

    user_id = data.get('user_id')
    asset_id = data.get('asset_id')
    oss_object_key = data.get('oss_object_key')
    parameters = data.get('parameters', {})

    # 确定使用的图片源
    picture_source = None
    picture_url = None

    # 1. 如果提供了 asset_id，从数据库获取
    if asset_id:
        mysql_row = MySQLService().fetch_asset_by_id(asset_id)
        if not mysql_row:
            return error_response('Asset not found', 404)

        if mysql_row['user_id'] != user_id:
            return error_response('Unauthorized: This asset does not belong to the user', 403)

        asset_data = MongoService().fetch_asset_data(asset_id)
        if not asset_data:
            return error_response('Asset data not found', 404)

        picture_source = 'asset'
        picture_url = asset_data.get('oss_url')
        oss_object_key = asset_data.get('oss_object_key')

    # 2. 如果提供了 oss_object_key，直接使用
    elif oss_object_key:
        picture_source = 'oss'
        # 获取图片 URL
        url_result = anime_tool_service.get_picture_url(oss_object_key)
        if url_result.get('success'):
            picture_url = url_result['url']
        else:
            return error_response(f"Failed to get picture URL: {url_result.get('error')}", 400)

    # 3. 如果提供了新文件，先上传到 OSS
    elif 'picture' in request.files:
        file = request.files['picture']
        if file.filename == '':
            return error_response('No file selected', 400)

        file_content = file.read()
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'
        object_key = anime_tool_service.generate_object_key(user_id, file_extension)

        upload_result = anime_tool_service.upload_picture(
            file_content=file_content,
            object_key=object_key,
            content_type=file.content_type or 'image/jpeg'
        )

        if not upload_result.get('success'):
            return error_response(f"Failed to upload picture: {upload_result.get('error')}", 500)

        picture_source = 'new_upload'
        picture_url = upload_result['url']
        oss_object_key = object_key

    else:
        return error_response('Must provide either asset_id, oss_object_key, or picture file', 400)

    # TODO: 实现图生视频的具体逻辑
    # 目前先返回一个框架响应
    task_id = str(uuid.uuid4())

    # 记录生成任务（可以存储到数据库用于后续查询）
    anime_task_data = {
        'task_id': task_id,
        'user_id': user_id,
        'source_type': picture_source,
        'source_asset_id': asset_id,
        'source_object_key': oss_object_key,
        'source_url': picture_url,
        'parameters': parameters,
        'status': 'pending',  # pending -> processing -> completed / failed
        'created_at': datetime.now().isoformat()
    }

    # TODO: 这里将来需要：
    # 1. 调用阿里云通义万相或其他视频生成 API
    # 2. 将任务状态存储到数据库
    # 3. 支持轮询任务状态接口
    # 4. 视频生成完成后存储结果并返回

    logger.info(f"Anime generation task created: {task_id}, source: {picture_source}")

    return api_response(
        success=True,
        message='Anime generation task created (placeholder - implementation pending)',
        data={
            'task_id': task_id,
            'status': 'pending',
            'source': {
                'type': picture_source,
                'asset_id': asset_id,
                'object_key': oss_object_key,
                'url': picture_url
            },
            'parameters': parameters,
            'note': 'This is a placeholder response. Video generation logic to be implemented.'
        },
        count=1
    )


@anime_tool_bp.route('/deletePicture', methods=['POST'])
@handle_errors
def delete_picture():
    """
    删除用户已上传的漫画图片

    请求参数：
    - asset_id: 资产 ID (必填)
    - user_id: 用户 ID (必填，用于权限验证)

    返回：
    - success: 是否删除成功
    - message: 删除结果信息
    """
    data = request.get_json()
    validate_required_fields(data, ['asset_id', 'user_id'])

    asset_id = data.get('asset_id')
    user_id = data.get('user_id')

    # 获取资产信息
    mysql_row = MySQLService().fetch_asset_by_id(asset_id)
    if not mysql_row:
        return error_response('Asset not found', 404)

    # 验证权限
    if mysql_row['user_id'] != user_id:
        return error_response('Unauthorized: This asset does not belong to the user', 403)

    # 获取 asset_data 中的 OSS 信息
    asset_data = MongoService().fetch_asset_data(asset_id)
    oss_object_key = asset_data.get('oss_object_key') if asset_data else None

    # 删除 OSS 中的图片
    if oss_object_key:
        try:
            delete_result = anime_tool_service.delete_picture(oss_object_key)
            if not delete_result.get('success'):
                logger.warning(f"Failed to delete picture from OSS: {delete_result.get('error')}")
                # 继续删除数据库记录，即使 OSS 删除失败
        except Exception as e:
            logger.error(f"Error deleting picture from OSS: {str(e)}")

    # 级联删除数据库中的记录
    try:
        MongoService().delete_asset_data(asset_id)
    except Exception as e:
        logger.error(f"Error deleting asset data from MongoDB: {str(e)}")

    deleted = MySQLService().delete_asset(asset_id)

    if deleted:
        return api_response(
            success=True,
            message='Picture deleted successfully',
            data=None,
            count=1
        )
    else:
        return error_response('Failed to delete asset record', 500)


@anime_tool_bp.route('/health', methods=['GET'])
@handle_errors
def health_check():
    """健康检查"""
    health_status = anime_tool_service.health_check()

    return api_response(
        success=True,
        message='Health check completed',
        data={
            'service': 'anime-tool',
            **health_status
        }
    )
