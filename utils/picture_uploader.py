"""
图片上传工具函数
提供统一的图片上传到 OSS 并创建 asset 记录的功能
"""
from flask import request
from utils.response_helper import error_response
from utils.constants import (
    AssetType, AssetDataType, RequestParams,
    Defaults, FileTypes
)
from db import MySQLService, MongoService, oss_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def upload_picture_file(file, user_id, work_id=None, return_error_response=True):
    """
    上传图片文件到 OSS 并创建 asset 记录

    Args:
        file: Werkzeug FileStorage 对象
        user_id: 用户 ID
        work_id: 作品 ID（可选）
        return_error_response: 是否返回 error_response（False 时返回 None）

    Returns:
        tuple: (picture_url, asset_id, error_response)
        - 成功：(url, asset_id, None)
        - 失败：(None, None, error_response) 或 (None, None, None)

    Raises:
        ValueError: 当文件无效时
    """
    if not file or file.filename == '':
        if return_error_response:
            return None, None, error_response('No file provided', 400)
        raise ValueError('No file provided')

    # 读取文件内容
    file_content = file.read()
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else Defaults.IMAGE_EXTENSION

    # 生成 OSS 对象键
    object_key = oss_service.generate_object_key(user_id, file_extension)

    # 上传到 OSS
    try:
        upload_result = oss_service.upload_picture(
            file_content=file_content,
            object_key=object_key,
            content_type=file.content_type or FileTypes.IMAGE_JPEG
        )
    except RuntimeError as e:
        logger.error(f"OSS service not available: {e}")
        if return_error_response:
            return None, None, error_response('Picture upload service not available (OSS not configured)', 503)
        raise RuntimeError('OSS service not available')

    if not upload_result.get('success'):
        if return_error_response:
            return None, None, error_response(f"Failed to upload picture: {upload_result.get('error')}", 500)
        raise RuntimeError(f"Failed to upload picture: {upload_result.get('error')}")

    # 创建 asset 记录
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
        if return_error_response:
            return None, None, error_response('Failed to create asset record', 500)
        raise

    return oss_url_for_db, asset_id, None
