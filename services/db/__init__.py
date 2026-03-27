"""
数据库访问层模块
按功能拆分的 MySQL 和 MongoDB 服务类
"""

# MySQL Services
from .base_service import mysql_base_service, MySQLBaseService, TABLE_WHITELIST
from .mysql_service import mysql_service, MySQLService
from .mongo_service import mongo_service, MongoService
from .user_service import user_service, UserService
from .asset_service import asset_service, AssetService
from .work_service import work_service, WorkService
from .chapter_service import chapter_service, ChapterService

# MongoDB Services
from .mongo_asset_service import asset_data_service, AssetDataService
from .mongo_work_service import work_details_service, WorkDetailsService


__all__ = [
    # MySQL
    'mysql_base_service',
    'MySQLBaseService',
    'TABLE_WHITELIST',
    'mysql_service',
    'MySQLService',
    'user_service',
    'UserService',
    'asset_service',
    'AssetService',
    'work_service',
    'WorkService',
    'chapter_service',
    'ChapterService',
    # MongoDB
    'mongo_service',
    'MongoService',
    'asset_data_service',
    'AssetDataService',
    'work_details_service',
    'WorkDetailsService',
]
