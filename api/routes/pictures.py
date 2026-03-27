# api/routes/pictures.py
"""
Picture Routes 模块
提供漫画图片上传、获取、删除等功能
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors
from utils.general_helper import validate_required_fields
from utils.constants import (
    AssetType, AssetDataType, RequestParams, ResponseMessage,
    Defaults, FileTypes, Pagination
)
from services.storage import oss_service
from services.db import MySQLService, MongoService
import logging
from datetime import datetime

picture_bp = Blueprint('picture', __name__)
logger = logging.getLogger(__name__)


@picture_bp.route('/uploadPicture', methods=['POST'])
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
    if RequestParams.PICTURE not in request.files:
        return error_response(ResponseMessage.MISSING_PICTURE, 400)

    file = request.files[RequestParams.PICTURE]
    if file.filename == '':
        return error_response(ResponseMessage.NO_FILE_SELECTED, 400)

    # 获取表单数据
    data = request.form
    validate_required_fields(data, [RequestParams.USER_ID])

    user_id = data.get(RequestParams.USER_ID)
    work_id = data.get(RequestParams.WORK_ID, None)

    # 读取文件内容
    file_content = file.read()
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else Defaults.IMAGE_EXTENSION

    # 生成 OSS 对象键
    object_key = oss_service.generate_object_key(user_id, file_extension)

    # 上传到 OSS
    upload_result = oss_service.upload_picture(
        file_content=file_content,
        object_key=object_key,
        content_type=file.content_type or FileTypes.IMAGE_JPEG
    )

    if not upload_result.get('success'):
        return error_response(f"Failed to upload picture: {upload_result.get('error')}", 500)

    # 创建 asset 记录（类型：picture）
    mysql_row = MySQLService().insert_asset(user_id, AssetType.PICTURE, work_id)
    asset_id = mysql_row['asset_id']

    # 处理 OSS URL，只保留 API 部分
    oss_url_for_db = upload_result['url'].split('?')[0]

    # 创建 asset_data 记录
    asset_data = {
        AssetDataType.TYPE: AssetType.PICTURE,
        AssetDataType.OSS_URL: oss_url_for_db,
        AssetDataType.OSS_OBJECT_KEY: object_key,
        AssetDataType.ORIGINAL_FILENAME: file.filename,
        AssetDataType.FILE_SIZE: len(file_content),
        AssetDataType.UPLOAD_TIMESTAMP: datetime.now().isoformat()
    }

    try:
        MongoService().insert_asset_data(asset_id, asset_data)
    except Exception as e:
        logger.error(f"Error inserting asset data to MongoDB: {str(e)}")
        # 回滚：删除 MySQL 和 OSS 中的数据
        MySQLService().delete_asset(asset_id)
        oss_service.delete_picture(object_key)
        return error_response('Failed to create asset record', 500)

    result = {
        RequestParams.ASSET_ID: asset_id,
        RequestParams.USER_ID: user_id,
        RequestParams.WORK_ID: work_id,
        'url': upload_result['url'],
        'object_key': object_key,
        RequestParams.ORIGINAL_FILENAME: file.filename,
        RequestParams.FILE_SIZE: len(file_content)
    }

    return api_response(
        success=True,
        message=ResponseMessage.UPLOAD_SUCCESS,
        data=result,
        count=1
    )


@picture_bp.route('/fetchPictureByAssetId', methods=['GET'])
@handle_errors
def fetch_picture_by_asset_id():
    """
    通过 asset_id 获取单条漫画图片信息

    请求参数：
    - asset_id: 资产 ID (必填)
    - user_id: 用户 ID (必填，用于权限验证)

    返回：
    - asset: 资产对象（包含 asset_id, user_id, work_id, asset_type, created_at, updated_at）
    - asset_data: 资产详情对象（包含 url, object_key, original_filename, file_size, upload_timestamp）
    """
    validate_required_fields(request.args, [RequestParams.ASSET_ID, RequestParams.USER_ID])

    asset_id = request.args.get(RequestParams.ASSET_ID)
    user_id = request.args.get(RequestParams.USER_ID)

    # 从 MySQL 获取资产记录
    mysql_row = MySQLService().fetch_asset_by_id(asset_id)

    if not mysql_row:
        return error_response(ResponseMessage.NOT_FOUND, 404)

    # 验证权限
    if mysql_row[RequestParams.USER_ID] != user_id:
        return error_response(ResponseMessage.UNAUTHORIZED, 403)

    # 获取 MongoDB 中的 asset_data
    asset_data = MongoService().fetch_asset_data(asset_id)

    # 构建标准 asset 格式的返回
    result = {
        'asset': {
            RequestParams.ASSET_ID: mysql_row[RequestParams.ASSET_ID],
            RequestParams.USER_ID: mysql_row[RequestParams.USER_ID],
            RequestParams.WORK_ID: mysql_row.get(RequestParams.WORK_ID),
            'asset_type': mysql_row.get('asset_type'),
            'created_at': mysql_row['created_at'],
            'updated_at': mysql_row['updated_at'],
            'asset_data': asset_data
        }
    }

    return api_response(
        success=True,
        message=ResponseMessage.FETCH_SUCCESS,
        data=result,
        count=1
    )


@picture_bp.route('/fetchPicturesByWorkId', methods=['GET'])
@handle_errors
def fetch_pictures_by_work_id():
    """
    通过 work_id 获取漫画图片列表（无或一或多）

    请求参数：
    - work_id: 作品 ID (必填)
    - user_id: 用户 ID (必填，用于权限验证)
    - limit: 返回数量限制 (可选，默认 100)
    - offset: 偏移量 (可选，默认 0)

    返回：
    - assets: 资产列表（每个元素包含 asset 和 asset_data）
    """
    validate_required_fields(request.args, [RequestParams.WORK_ID, RequestParams.USER_ID])

    work_id = request.args.get(RequestParams.WORK_ID)
    user_id = request.args.get(RequestParams.USER_ID)

    # 解析分页参数
    try:
        limit = int(request.args.get(RequestParams.LIMIT, str(Pagination.DEFAULT_LIMIT)))
        offset = int(request.args.get(RequestParams.OFFSET, str(Pagination.DEFAULT_OFFSET)))
    except ValueError:
        return error_response('limit and offset must be integers', 400)

    # 从 MySQL 获取资产列表（通过 work_id 筛选）
    mysql_rows = MySQLService().fetch_assets(
        user_id, asset_type=AssetType.COMIC, work_id=work_id, limit=limit, offset=offset
    )

    if not mysql_rows:
        return api_response(
            success=True,
            message='No pictures found',
            data=[],
            count=0
        )

    # 获取 MongoDB 中的 asset_data
    asset_ids = [row[RequestParams.ASSET_ID] for row in mysql_rows]
    asset_data_map = MongoService().fetch_multiple_asset_data(asset_ids)

    # 构建返回结果 - 标准 asset 格式
    results = []
    for row in mysql_rows:
        asset_data = asset_data_map.get(row[RequestParams.ASSET_ID], {})
        results.append({
            'asset': {
                RequestParams.ASSET_ID: row[RequestParams.ASSET_ID],
                RequestParams.USER_ID: row[RequestParams.USER_ID],
                RequestParams.WORK_ID: row.get(RequestParams.WORK_ID),
                'asset_type': row.get('asset_type'),
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'asset_data': asset_data
            },
        })

    return api_response(
        success=True,
        message='Pictures fetched successfully',
        data=results,
        count=len(results)
    )


@picture_bp.route('/fetchPicturesByUserId', methods=['GET'])
@handle_errors
def fetch_pictures_by_user_id():
    """
    通过 user_id 获取漫画图片列表（无或一或多）

    请求参数：
    - user_id: 用户 ID (必填)
    - work_id: 作品 ID (可选，筛选特定作品的图片)
    - limit: 返回数量限制 (可选，默认 100)
    - offset: 偏移量 (可选，默认 0)

    返回：
    - assets: 资产列表（每个元素包含 asset 和 asset_data）
    """
    validate_required_fields(request.args, [RequestParams.USER_ID])

    user_id = request.args.get(RequestParams.USER_ID)
    work_id = request.args.get(RequestParams.WORK_ID, None)

    # 解析分页参数
    try:
        limit = int(request.args.get(RequestParams.LIMIT, str(Pagination.DEFAULT_LIMIT)))
        offset = int(request.args.get(RequestParams.OFFSET, str(Pagination.DEFAULT_OFFSET)))
    except ValueError:
        return error_response('limit and offset must be integers', 400)

    # 从 MySQL 获取资产列表
    mysql_rows = MySQLService().fetch_assets(
        user_id, asset_type=AssetType.COMIC, work_id=work_id, limit=limit, offset=offset
    )

    if not mysql_rows:
        return api_response(
            success=True,
            message='No pictures found',
            data=[],
            count=0
        )

    # 获取 MongoDB 中的 asset_data
    asset_ids = [row[RequestParams.ASSET_ID] for row in mysql_rows]
    asset_data_map = MongoService().fetch_multiple_asset_data(asset_ids)

    # 构建返回结果 - 标准 asset 格式
    results = []
    for row in mysql_rows:
        asset_data = asset_data_map.get(row[RequestParams.ASSET_ID], {})
        results.append({
            'asset': {
                RequestParams.ASSET_ID: row[RequestParams.ASSET_ID],
                RequestParams.USER_ID: row[RequestParams.USER_ID],
                RequestParams.WORK_ID: row.get(RequestParams.WORK_ID),
                'asset_type': row.get('asset_type'),
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'asset_data': asset_data
            },
        })

    return api_response(
        success=True,
        message='Pictures fetched successfully',
        data=results,
        count=len(results)
    )


@picture_bp.route('/deletePicture', methods=['POST'])
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
    validate_required_fields(data, [RequestParams.ASSET_ID, RequestParams.USER_ID])

    asset_id = data.get(RequestParams.ASSET_ID)
    user_id = data.get(RequestParams.USER_ID)

    # 获取资产信息
    mysql_row = MySQLService().fetch_asset_by_id(asset_id)
    if not mysql_row:
        return error_response(ResponseMessage.NOT_FOUND, 404)

    # 验证权限
    if mysql_row[RequestParams.USER_ID] != user_id:
        return error_response(ResponseMessage.UNAUTHORIZED, 403)

    # 获取 asset_data 中的 OSS 信息
    asset_data = MongoService().fetch_asset_data(asset_id)
    oss_object_key = asset_data.get(RequestParams.OSS_OBJECT_KEY) if asset_data else None

    # 删除 OSS 中的图片
    if oss_object_key:
        try:
            delete_result = oss_service.delete_picture(oss_object_key)
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
            message=ResponseMessage.DELETE_SUCCESS,
            data=None,
            count=1
        )
    else:
        return error_response('Failed to delete asset record', 500)


@picture_bp.route('/health', methods=['GET'])
@handle_errors
def health_check():
    """健康检查"""
    health_status = oss_service.health_check()

    return api_response(
        success=True,
        message=ResponseMessage.HEALTH_CHECK_SUCCESS,
        data={
            'service': 'picture',
            **health_status
        }
    )
