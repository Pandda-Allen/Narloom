"""
OSS 服务模块
统一管理阿里云 OSS 服务的文件上传、下载、删除等操作
作为路由层与底层存储服务之间的中间层，类似 MySQLService 和 MongoService 的定位

架构：
- oss_service: 统一对外接口，路由层唯一调用入口
- picture_service: 具体执行图片相关的 OSS 操作
- video_service: 具体执行视频相关的 OSS 操作
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class OSSService:
    """
    OSS 服务类（单例模式）
    封装所有涉及 OSS 对象存储的操作，作为路由层与底层服务之间的中间层
    """

    _instance = None
    _initialized = False
    _picture_service = None
    _video_service = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_app(self, app):
        """初始化 OSS 服务"""
        with app.app_context():
            self._initialize()

    def _initialize(self):
        """初始化底层服务"""
        if self._initialized:
            return

        from .picture import picture_service
        from .video import video_service

        self._picture_service = picture_service
        self._video_service = video_service

        # 触发底层服务初始化
        if not self._picture_service._initialized:
            self._picture_service.init_app(self._get_app())
        if not self._video_service._initialized:
            self._video_service.init_app(self._get_app())

        self._initialized = True
        logger.info("OSS Service initialized successfully (Picture + Video services)")

    def _get_app(self):
        """获取当前 Flask 应用"""
        from flask import current_app
        return current_app

    @property
    def _initialized(self):
        """代理到底层服务的初始化状态"""
        return self.__class__._initialized

    @_initialized.setter
    def _initialized(self, value):
        self.__class__._initialized = value

    def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            raise RuntimeError("OSS Service not initialized. Call init_app first.")

    # ==================== 图片操作（委托给 picture_service）====================
    def upload_picture(self, file_content: bytes, object_key: str,
                       content_type: str = 'image/jpeg') -> Dict:
        """上传图片到阿里云 OSS"""
        self._ensure_initialized()
        return self._picture_service.upload_picture(file_content, object_key, content_type)

    def upload_picture_from_file(self, file_path: str, object_key: str,
                                  content_type: str = 'image/jpeg') -> Dict:
        """从本地文件路径上传图片"""
        self._ensure_initialized()
        return self._picture_service.upload_picture_from_file(file_path, object_key, content_type)

    def get_picture_url(self, object_key: str, expires: int = 3600) -> Dict:
        """获取图片的访问 URL"""
        self._ensure_initialized()
        return self._picture_service.get_picture_url(object_key, expires)

    def download_picture(self, object_key: str, local_file_path: str) -> Dict:
        """下载图片到本地"""
        self._ensure_initialized()
        return self._picture_service.download_picture(object_key, local_file_path)

    def get_picture_content(self, object_key: str) -> Dict:
        """获取图片的二进制内容"""
        self._ensure_initialized()
        return self._picture_service.get_picture_content(object_key)

    def delete_picture(self, object_key: str) -> Dict:
        """删除 OSS 中的图片"""
        self._ensure_initialized()
        return self._picture_service.delete_picture(object_key)

    def delete_pictures_batch(self, object_keys: List[str]) -> Dict:
        """批量删除图片"""
        self._ensure_initialized()
        return self._picture_service.delete_pictures_batch(object_keys)

    def list_pictures(self, prefix: str = 'comic/', max_codes: int = 100,
                      marker: str = '') -> Dict:
        """列出 OSS 中的图片"""
        self._ensure_initialized()
        return self._picture_service.list_pictures(prefix, max_codes, marker)

    # ==================== 视频操作（委托给 video_service）====================
    def upload_video(self, video_content: bytes, object_key: str,
                     content_type: str = 'video/mp4') -> Dict:
        """上传视频到 OSS"""
        self._ensure_initialized()
        return self._video_service.upload_video(video_content, object_key, content_type)

    def upload_video_from_file(self, file_path: str, object_key: str,
                                content_type: str = 'video/mp4') -> Dict:
        """从本地文件路径上传视频"""
        self._ensure_initialized()
        return self._video_service.upload_video_from_file(file_path, object_key, content_type)

    def get_video_url(self, object_key: str, expires: int = 3600) -> Dict:
        """获取视频的访问 URL"""
        self._ensure_initialized()
        return self._video_service.get_video_url(object_key, expires)

    def download_video(self, object_key: str, local_file_path: str) -> Dict:
        """下载视频到本地"""
        self._ensure_initialized()
        return self._video_service.download_video(object_key, local_file_path)

    def get_video_content(self, object_key: str) -> Dict:
        """获取视频的二进制内容"""
        self._ensure_initialized()
        return self._video_service.get_video_content(object_key)

    def delete_video(self, object_key: str) -> Dict:
        """删除 OSS 中的视频"""
        self._ensure_initialized()
        return self._video_service.delete_video(object_key)

    def delete_videos_batch(self, object_keys: List[str]) -> Dict:
        """批量删除视频"""
        self._ensure_initialized()
        return self._video_service.delete_videos_batch(object_keys)

    def list_videos(self, prefix: str = 'video/', max_codes: int = 100,
                    marker: str = '') -> Dict:
        """列出 OSS 中的视频"""
        self._ensure_initialized()
        return self._video_service.list_videos(prefix, max_codes, marker)

    def save_video_from_url(self, video_url: str, object_key: str) -> Dict:
        """从 URL 下载视频并保存到 OSS"""
        self._ensure_initialized()
        return self._video_service.save_video_from_url(video_url, object_key)

    # ==================== 辅助方法 ====================
    def generate_picture_object_key(self, user_id: str, file_extension: str,
                                     asset_id: str = None) -> str:
        """
        生成图片文件的 OSS 对象键

        Args:
            user_id: 用户 ID
            file_extension: 文件扩展名
            asset_id: 资产 ID（可选）

        Returns:
            str: 生成的对象键
        """
        if asset_id:
            return f"image/{user_id}/{asset_id}.{file_extension}"

        from datetime import datetime
        from uuid import uuid4
        now = datetime.now()
        unique_id = str(uuid4())[:8]
        return f"image/{user_id}/{now.year}/{now.month:02d}/{unique_id}.{file_extension}"

    def generate_video_object_key(self, user_id: str, asset_id: str = None) -> str:
        """
        生成视频文件的 OSS 对象键

        Args:
            user_id: 用户 ID
            asset_id: 资产 ID（可选）

        Returns:
            str: 生成的对象键
        """
        self._ensure_initialized()
        return self._video_service.generate_video_object_key(user_id, asset_id)

    def generate_object_key(self, user_id: str, file_extension: str,
                            file_type: str = 'image') -> str:
        """
        生成唯一的对象键（文件路径）

        Args:
            user_id: 用户 ID
            file_extension: 文件扩展名
            file_type: 文件类型（image/video）

        Returns:
            str: 生成的对象键
        """
        from datetime import datetime
        from uuid import uuid4
        now = datetime.now()
        unique_id = str(uuid4())[:8]
        return f"{file_type}/{user_id}/{now.year}/{now.month:02d}/{unique_id}.{file_extension}"

    def health_check(self) -> Dict:
        """健康检查"""
        self._ensure_initialized()
        picture_status = self._picture_service.health_check()
        video_status = self._video_service.health_check()

        return {
            'status': 'healthy' if picture_status.get('status') == 'healthy' and video_status.get('status') == 'healthy' else 'unhealthy',
            'picture_service': picture_status,
            'video_service': video_status
        }


# 全局实例
oss_service = OSSService()
