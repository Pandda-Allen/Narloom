"""
阿里云 OSS 服务类，负责漫画图片的上传、下载、删除操作。
使用单例模式，线程安全。
"""
import os
import oss2
from typing import Optional, Dict, List, BinaryIO
from .base_service import BaseService


class AnimeToolService(BaseService):
    """阿里云 OSS 服务类，负责漫画图片的存储操作"""

    _instance = None
    _initialized = False
    _auth = None
    _bucket = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ---------- 初始化 ----------
    def init_app(self, app):
        with app.app_context():
            self._initialize()

    def _initialize(self):
        if self._initialized:
            return

        # 获取配置
        endpoint = self._get_config('ALIYUN_OSS_ENDPOINT')
        access_key_id = self._get_config('ALIYUN_OSS_ACCESS_KEY_ID')
        access_key_secret = self._get_config('ALIYUN_OSS_ACCESS_KEY_SECRET')
        bucket_name = self._get_config('ALIYUN_OSS_BUCKET_NAME')
        cdn_domain = self._get_config('ALIYUN_OSS_CDN_DOMAIN', '')

        if not all([endpoint, access_key_id, access_key_secret, bucket_name]):
            self._log("Aliyun OSS configuration incomplete", level='error')
            raise RuntimeError("Aliyun OSS configuration incomplete")

        try:
            # 初始化 OSS 认证
            self._auth = oss2.Auth(access_key_id, access_key_secret)
            # 初始化 Bucket
            self._bucket = oss2.Bucket(self._auth, endpoint, bucket_name)
            self._cdn_domain = cdn_domain
            self._endpoint = endpoint
            self._bucket_name = bucket_name
            self._initialized = True
            self._log("Aliyun OSS service initialized successfully")
        except Exception as e:
            self._log(f"Error initializing Aliyun OSS service: {e}", level='error')
            raise

    def _ensure_bucket(self):
        """确保 bucket 可用"""
        if self._bucket is None:
            self._initialize()
        return self._bucket

    # ---------- 图片上传操作 ----------
    def upload_picture(self, file_content: bytes, object_key: str, content_type: str = 'image/jpeg') -> Dict:
        """
        上传图片到阿里云 OSS

        Args:
            file_content: 图片文件的二进制内容
            object_key: OSS 中的对象键（路径）
            content_type: 文件类型

        Returns:
            Dict: 包含上传结果和访问 URL 的字典
        """
        bucket = self._ensure_bucket()

        try:
            # 上传文件
            result = bucket.put_object(object_key, file_content, headers={'Content-Type': content_type})

            if result.status == 200:
                # 生成访问 URL
                url = self._get_file_url(object_key)
                return {
                    'success': True,
                    'object_key': object_key,
                    'url': url,
                    'message': 'Picture uploaded successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Upload failed with status {result.status}',
                    'object_key': object_key
                }
        except Exception as e:
            self._log(f"Error uploading picture to OSS: {str(e)}", level='error')
            return {
                'success': False,
                'error': str(e),
                'object_key': object_key
            }

    def upload_picture_from_file(self, file_path: str, object_key: str, content_type: str = 'image/jpeg') -> Dict:
        """
        从本地文件路径上传图片

        Args:
            file_path: 本地文件路径
            object_key: OSS 中的对象键
            content_type: 文件类型

        Returns:
            Dict: 包含上传结果和访问 URL 的字典
        """
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            return self.upload_picture(file_content, object_key, content_type)
        except Exception as e:
            self._log(f"Error reading file {file_path}: {str(e)}", level='error')
            return {
                'success': False,
                'error': str(e),
                'object_key': object_key
            }

    # ---------- 图片获取操作 ----------
    def get_picture_url(self, object_key: str, expires: int = 3600) -> Dict:
        """
        获取图片的访问 URL

        Args:
            object_key: OSS 中的对象键
            expires: URL 过期时间（秒），默认 1 小时

        Returns:
            Dict: 包含 URL 的字典
        """
        try:
            url = self._get_file_url(object_key, expires)
            return {
                'success': True,
                'url': url,
                'object_key': object_key
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'object_key': object_key
            }

    def download_picture(self, object_key: str, local_file_path: str) -> Dict:
        """
        下载图片到本地

        Args:
            object_key: OSS 中的对象键
            local_file_path: 本地保存路径

        Returns:
            Dict: 包含下载结果的字典
        """
        bucket = self._ensure_bucket()

        try:
            bucket.get_object_to_file(object_key, local_file_path)
            return {
                'success': True,
                'message': 'Picture downloaded successfully',
                'local_path': local_file_path,
                'object_key': object_key
            }
        except Exception as e:
            self._log(f"Error downloading picture from OSS: {str(e)}", level='error')
            return {
                'success': False,
                'error': str(e),
                'object_key': object_key
            }

    def get_picture_content(self, object_key: str) -> Dict:
        """
        获取图片的二进制内容

        Args:
            object_key: OSS 中的对象键

        Returns:
            Dict: 包含图片二进制内容的字典
        """
        bucket = self._ensure_bucket()

        try:
            result = bucket.get_object(object_key)
            content = result.read()
            return {
                'success': True,
                'content': content,
                'content_type': result.headers.get('Content-Type', 'image/jpeg'),
                'object_key': object_key
            }
        except Exception as e:
            self._log(f"Error getting picture content from OSS: {str(e)}", level='error')
            return {
                'success': False,
                'error': str(e),
                'object_key': object_key
            }

    # ---------- 图片删除操作 ----------
    def delete_picture(self, object_key: str) -> Dict:
        """
        删除 OSS 中的图片

        Args:
            object_key: OSS 中的对象键

        Returns:
            Dict: 包含删除结果的字典
        """
        bucket = self._ensure_bucket()

        try:
            result = bucket.delete_object(object_key)
            if result.status == 204:
                return {
                    'success': True,
                    'message': 'Picture deleted successfully',
                    'object_key': object_key
                }
            else:
                return {
                    'success': False,
                    'error': f'Delete failed with status {result.status}',
                    'object_key': object_key
                }
        except Exception as e:
            self._log(f"Error deleting picture from OSS: {str(e)}", level='error')
            return {
                'success': False,
                'error': str(e),
                'object_key': object_key
            }

    def delete_pictures_batch(self, object_keys: List[str]) -> Dict:
        """
        批量删除图片

        Args:
            object_keys: OSS 对象键列表

        Returns:
            Dict: 包含批量删除结果的字典
        """
        bucket = self._ensure_bucket()

        try:
            result = bucket.batch_delete_objects(object_keys)
            return {
                'success': True,
                'deleted_keys': result.deleted_keys,
                'message': f'Successfully deleted {len(result.deleted_keys)} pictures'
            }
        except Exception as e:
            self._log(f"Error batch deleting pictures from OSS: {str(e)}", level='error')
            return {
                'success': False,
                'error': str(e),
                'deleted_keys': []
            }

    # ---------- 图片列表操作 ----------
    def list_pictures(self, prefix: str = 'comic/', max_keys: int = 100, marker: str = '') -> Dict:
        """
        列出 OSS 中的图片

        Args:
            prefix: 对象键前缀，用于筛选特定目录
            max_keys: 最大返回数量
            marker: 分页标记

        Returns:
            Dict: 包含图片列表的字典
        """
        bucket = self._ensure_bucket()

        try:
            result = bucket.list_objects(prefix=prefix, max_keys=max_keys, marker=marker)

            pictures = []
            for obj in result.object_list:
                pictures.append({
                    'object_key': obj.key,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag,
                    'url': self._get_file_url(obj.key)
                })

            return {
                'success': True,
                'pictures': pictures,
                'is_truncated': result.is_truncated,
                'next_marker': result.next_marker if result.is_truncated else '',
                'count': len(pictures)
            }
        except Exception as e:
            self._log(f"Error listing pictures from OSS: {str(e)}", level='error')
            return {
                'success': False,
                'error': str(e),
                'pictures': [],
                'count': 0
            }

    # ---------- 辅助方法 ----------
    def _get_file_url(self, object_key: str, expires: int = 3600) -> str:
        """
        生成文件访问 URL

        Args:
            object_key: OSS 中的对象键
            expires: URL 过期时间（秒）

        Returns:
            str: 文件访问 URL
        """
        # 如果配置了 CDN 域名，使用 CDN 域名
        if self._cdn_domain:
            return f"https://{self._cdn_domain}/{object_key}"

        # 否则生成签名 URL
        bucket = self._ensure_bucket()
        return bucket.sign_url('GET', object_key, expires)

    def generate_object_key(self, user_id: str, file_extension: str) -> str:
        """
        生成唯一的对象键（文件路径）

        Args:
            user_id: 用户 ID
            file_extension: 文件扩展名

        Returns:
            str: 生成的对象键
        """
        import uuid
        from datetime import datetime

        # 生成格式：comic/{user_id}/{year}/{month}/{uuid}.{ext}
        now = datetime.now()
        unique_id = str(uuid.uuid4())[:8]
        object_key = f"comic/{user_id}/{now.year}/{now.month:02d}/{unique_id}.{file_extension}"

        return object_key

    def health_check(self) -> Dict:
        """健康检查"""
        if not self._initialized:
            return {
                'status': 'not_initialized',
                'message': 'Aliyun OSS service not initialized'
            }

        try:
            # 尝试获取 bucket 信息
            bucket = self._ensure_bucket()
            bucket.get_bucket_info()
            return {
                'status': 'healthy',
                'message': 'Aliyun OSS connection successful',
                'bucket': self._bucket_name,
                'endpoint': self._endpoint
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': str(e)
            }


# 全局实例
anime_tool_service = AnimeToolService()
