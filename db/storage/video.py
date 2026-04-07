"""
Video Service 模块
统一管理阿里云 OSS 服务的视频文件上传、下载、删除等操作
作为路由层与底层 OSS 服务之间的中间层，专门处理视频相关文件
"""
import logging
import requests
from typing import Dict, List
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)


class VideoService:
    """
    Video 服务类（单例模式）
    封装所有涉及 OSS 视频文件存储的操作
    """

    _instance = None
    _initialized = False
    _picture_service = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_app(self, app):
        """初始化 Video 服务"""
        with app.app_context():
            self._initialize()

    def _initialize(self):
        """初始化底层 PictureService（用于实际 OSS 操作）"""
        if self._initialized:
            return

        from .picture_service import picture_service
        self._picture_service = picture_service

        # 触发底层服务初始化
        if not self._picture_service._initialized:
            self._picture_service.init_app(self._get_app())

        self._initialized = True
        logger.info("Video Service initialized successfully")

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

    # ==================== 视频上传操作 ====================
    def upload_video(self, video_content: bytes, object_key: str,
                     content_type: str = 'video/mp4') -> Dict:
        """
        上传视频到阿里云 OSS

        Args:
            video_content: 视频文件的二进制内容
            object_key: OSS 中的对象键（路径）
            content_type: 文件类型

        Returns:
            Dict: 包含上传结果和访问 URL 的字典
        """
        self._ensure_initialized()
        # 视频上传复用 picture_service 的 upload_picture 方法
        return self._picture_service.upload_picture(video_content, object_key, content_type)

    def upload_video_from_file(self, file_path: str, object_key: str,
                                content_type: str = 'video/mp4') -> Dict:
        """
        从本地文件路径上传视频

        Args:
            file_path: 本地文件路径
            object_key: OSS 中的对象键
            content_type: 文件类型

        Returns:
            Dict: 包含上传结果和访问 URL 的字典
        """
        self._ensure_initialized()
        return self._picture_service.upload_picture_from_file(file_path, object_key, content_type)

    # ==================== 视频获取操作 ====================
    def get_video_url(self, object_key: str, expires: int = 3600) -> Dict:
        """
        获取视频的访问 URL

        Args:
            object_key: OSS 中的对象键
            expires: URL 过期时间（秒），默认 1 小时

        Returns:
            Dict: 包含 URL 的字典
        """
        self._ensure_initialized()
        return self._picture_service.get_picture_url(object_key, expires)

    def download_video(self, object_key: str, local_file_path: str) -> Dict:
        """
        下载视频到本地

        Args:
            object_key: OSS 中的对象键
            local_file_path: 本地保存路径

        Returns:
            Dict: 包含下载结果的字典
        """
        self._ensure_initialized()
        return self._picture_service.download_picture(object_key, local_file_path)

    def get_video_content(self, object_key: str) -> Dict:
        """
        获取视频的二进制内容

        Args:
            object_key: OSS 中的对象键

        Returns:
            Dict: 包含视频二进制内容的字典
        """
        self._ensure_initialized()
        return self._picture_service.get_picture_content(object_key)

    # ==================== 视频删除操作 ====================
    def delete_video(self, object_key: str) -> Dict:
        """
        删除 OSS 中的视频

        Args:
            object_key: OSS 中的对象键

        Returns:
            Dict: 包含删除结果的字典
        """
        self._ensure_initialized()
        return self._picture_service.delete_picture(object_key)

    def delete_videos_batch(self, object_keys: List[str]) -> Dict:
        """
        批量删除视频

        Args:
            object_keys: OSS 对象键列表

        Returns:
            Dict: 包含批量删除结果的字典
        """
        self._ensure_initialized()
        return self._picture_service.delete_pictures_batch(object_keys)

    # ==================== 视频列表操作 ====================
    def list_videos(self, prefix: str = 'video/', max_codes: int = 100,
                    marker: str = '') -> Dict:
        """
        列出 OSS 中的视频

        Args:
            prefix: 对象键前缀，用于筛选特定目录
            max_codes: 最大返回数量
            marker: 分页标记

        Returns:
            Dict: 包含视频列表的字典
        """
        self._ensure_initialized()
        return self._picture_service.list_pictures(prefix, max_codes, marker)

    # ==================== 视频 URL 保存操作 ====================
    def save_video_from_url(self, video_url: str, object_key: str) -> Dict:
        """
        从 URL 下载视频并保存到 OSS

        Args:
            video_url: 视频的临时 URL
            object_key: OSS 中的对象键

        Returns:
            Dict: 包含保存结果的字典
        """
        self._ensure_initialized()

        try:
            # 下载视频内容
            logger.info(f"Downloading video from: {video_url}")
            response = requests.get(video_url, timeout=60)

            if response.status_code != 200:
                logger.error(f"Failed to download video: HTTP {response.status_code}")
                return {
                    'success': False,
                    'error': f'Failed to download video: HTTP {response.status_code}'
                }

            video_content = response.content
            logger.info(f"Video downloaded successfully, size: {len(video_content)} bytes")

            # 上传到 OSS
            upload_result = self.upload_video(video_content, object_key)

            if upload_result.get('success'):
                logger.info(f"Video uploaded to OSS: {object_key}")
                return {
                    'success': True,
                    'oss_object_key': object_key,
                    'oss_url': upload_result.get('url'),
                    'message': 'Video saved to OSS successfully'
                }
            else:
                logger.error(f"Failed to upload video to OSS: {upload_result.get('error')}")
                return {
                    'success': False,
                    'error': f"Failed to upload to OSS: {upload_result.get('error')}"
                }

        except requests.RequestException as e:
            logger.error(f"Request error while downloading video: {e}")
            return {
                'success': False,
                'error': f'Failed to download video: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error saving video to OSS: {e}")
            return {
                'success': False,
                'error': f'Error saving video: {str(e)}'
            }

    # ==================== 辅助方法 ====================
    def generate_object_key(self, user_id: str, file_extension: str = 'mp4') -> str:
        """
        生成唯一的视频对象键（文件路径）

        Args:
            user_id: 用户 ID
            file_extension: 文件扩展名，默认 mp4

        Returns:
            str: 生成的对象键
        """
        now = datetime.now()
        unique_id = str(uuid4())[:8]
        return f"video/{user_id}/{now.year}/{now.month:02d}/{unique_id}.{file_extension}"

    def generate_video_object_key(self, user_id: str, asset_id: str = None) -> str:
        """
        生成视频文件的 OSS 对象键

        Args:
            user_id: 用户 ID
            asset_id: 资产 ID（可选）

        Returns:
            str: 生成的对象键
        """
        if asset_id:
            return f"video/{user_id}/{asset_id}.mp4"

        now = datetime.now()
        unique_id = str(uuid4())[:8]
        return f"video/{user_id}/{now.year}/{now.month:02d}/{unique_id}.mp4"

    def health_check(self) -> Dict:
        """健康检查"""
        self._ensure_initialized()
        return self._picture_service.health_check()

    def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            raise RuntimeError("Video Service not initialized. Call init_app first.")


# 全局实例
video_service = VideoService()
