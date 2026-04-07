"""
数据库访问层模块
按功能拆分的 MySQL 和 MongoDB 服务类，以及 OSS 存储服务
"""

# MySQL Services
from .base_service import mysql_base_service, MySQLBaseService, TABLE_WHITELIST
from .user import user_service, UserService
from .asset import asset_service, AssetService
from .work import work_service, WorkService
from .novel import novel_service, NovelService
from .anime import anime_service, AnimeService

# MongoDB Services
from .mongo_asset import asset_data_service, AssetDataService
from .mongo_work import work_details_service, WorkDetailsService
from .mongo_novel import novel_details_service, NovelDetailsService
from .mongo_anime import anime_details_service, AnimeDetailsService

# Storage/OSS Services
from .storage.oss import oss_service, OSSService
from .storage.picture import picture_service, PictureService
from .storage.video import video_service, VideoService

# Compatibility wrappers - lazy import to avoid circular imports
def __getattr__(name):
    """Lazy import for compatibility wrappers"""
    if name in ('MySQLService', 'mysql_service'):
        from services.mysql_service import MySQLService, mysql_service
        return MySQLService if name == 'MySQLService' else mysql_service
    if name in ('MongoService', 'mongo_service'):
        from services.mongo_service import MongoService, mongo_service
        return MongoService if name == 'MongoService' else mongo_service
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # MySQL
    'mysql_base_service',
    'MySQLBaseService',
    'TABLE_WHITELIST',
    'user_service',
    'UserService',
    'asset_service',
    'AssetService',
    'work_service',
    'WorkService',
    'novel_service',
    'NovelService',
    'anime_service',
    'AnimeService',
    'MySQLService',
    'mysql_service',
    # MongoDB
    'asset_data_service',
    'AssetDataService',
    'work_details_service',
    'WorkDetailsService',
    'novel_details_service',
    'NovelDetailsService',
    'anime_details_service',
    'AnimeDetailsService',
    'MongoService',
    'mongo_service',
    # Storage/OSS
    'oss_service',
    'OSSService',
    'picture_service',
    'PictureService',
    'video_service',
    'VideoService',
]
