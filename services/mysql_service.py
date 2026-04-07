"""
MySQL 服务兼容性封装模块
为保持向后兼容，将所有服务方法聚合到 MySQLService 类中
新代码建议直接使用 services.db 中的具体 service
"""
from .db import (
    mysql_base_service,
    user_service,
    asset_service,
    work_service,
    chapter_service,
    shot_service,
    TABLE_WHITELIST
)
from .db.base_service import MySQLBaseService


class MySQLService:
    """
    MySQL 服务兼容类（聚合所有 service 方法）

    注意：这是为了保持向后兼容的封装层
    新代码建议直接使用 services.db 中的具体 service
    """

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_app(self, app):
        """初始化所有 service"""
        # 只需要初始化基础服务，其他 service 共享同一个数据库连接
        mysql_base_service.init_app(app)

    @property
    def _initialized(self):
        """代理到底层 service 的初始化状态"""
        return mysql_base_service._initialized

    # ========== 以下方法委托给对应的 service ==========

    # --- User 方法 ---
    def insert_user(self, *args, **kwargs):
        return user_service.insert_user(*args, **kwargs)

    def update_user(self, *args, **kwargs):
        return user_service.update_user(*args, **kwargs)

    def fetch_user_by_id(self, *args, **kwargs):
        return user_service.fetch_user_by_id(*args, **kwargs)

    def fetch_user_by_email(self, *args, **kwargs):
        return user_service.fetch_user_by_email(*args, **kwargs)

    def register_user(self, *args, **kwargs):
        return user_service.register_user(*args, **kwargs)

    def authenticate_user(self, *args, **kwargs):
        return user_service.authenticate_user(*args, **kwargs)

    def delete_user(self, *args, **kwargs):
        return user_service.delete_user(*args, **kwargs)

    def update_user_last_login(self, *args, **kwargs):
        return user_service.update_user_last_login(*args, **kwargs)

    # --- Asset 方法 ---
    def insert_asset(self, *args, **kwargs):
        return asset_service.insert_asset(*args, **kwargs)

    def update_asset(self, *args, **kwargs):
        return asset_service.update_asset(*args, **kwargs)

    def delete_asset(self, *args, **kwargs):
        return asset_service.delete_asset(*args, **kwargs)

    def fetch_asset_by_id(self, *args, **kwargs):
        return asset_service.fetch_asset_by_id(*args, **kwargs)

    def fetch_assets(self, *args, **kwargs):
        return asset_service.fetch_assets(*args, **kwargs)

    # --- Work 方法 ---
    def insert_work(self, *args, **kwargs):
        return work_service.insert_work(*args, **kwargs)

    def update_work(self, *args, **kwargs):
        return work_service.update_work(*args, **kwargs)

    def fetch_work_by_id(self, *args, **kwargs):
        return work_service.fetch_work_by_id(*args, **kwargs)

    def fetch_works_by_author_id(self, *args, **kwargs):
        return work_service.fetch_works_by_author_id(*args, **kwargs)

    def delete_work(self, *args, **kwargs):
        return work_service.delete_work(*args, **kwargs)

    # --- Chapter 方法 ---
    def insert_chapter(self, *args, **kwargs):
        return chapter_service.insert_chapter(*args, **kwargs)

    def update_chapter(self, *args, **kwargs):
        return chapter_service.update_chapter(*args, **kwargs)

    def fetch_chapter_by_id(self, *args, **kwargs):
        return chapter_service.fetch_chapter_by_id(*args, **kwargs)

    def fetch_chapters_by_work_id(self, *args, **kwargs):
        return chapter_service.fetch_chapters_by_work_id(*args, **kwargs)

    def delete_chapter(self, *args, **kwargs):
        return chapter_service.delete_chapter(*args, **kwargs)

    # --- Shot 方法 ---
    def insert_shot(self, *args, **kwargs):
        return shot_service.insert_shot(*args, **kwargs)

    def update_shot(self, *args, **kwargs):
        return shot_service.update_shot(*args, **kwargs)

    def fetch_shot_by_id(self, *args, **kwargs):
        return shot_service.fetch_shot_by_id(*args, **kwargs)

    def fetch_shots_by_work_id(self, *args, **kwargs):
        return shot_service.fetch_shots_by_work_id(*args, **kwargs)

    def delete_shot(self, *args, **kwargs):
        return shot_service.delete_shot(*args, **kwargs)


# 保持单例模式
mysql_service = MySQLService()
