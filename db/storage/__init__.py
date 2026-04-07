"""
存储服务层模块
统一管理阿里云 OSS 服务的文件上传、下载、删除等操作

架构：
- oss_service: 统一对外接口，路由层唯一调用入口
- picture_service: 具体执行图片相关的 OSS 操作
- video_service: 具体执行视频相关的 OSS 操作
"""

from .oss import oss_service, OSSService
from .picture import picture_service, PictureService
from .video import video_service, VideoService

__all__ = [
    # OSS Service (统一接口)
    'oss_service',
    'OSSService',
    # Picture Service (图片操作)
    'picture_service',
    'PictureService',
    # Video Service (视频操作)
    'video_service',
    'VideoService',
]
