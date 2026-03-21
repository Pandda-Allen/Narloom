"""
MongoDB 服务兼容性封装模块
为保持向后兼容，将所有服务方法聚合到 MongoService 类中
新代码建议直接使用 services.db 中的具体 service
"""
from .db.mongo_asset_service import asset_data_service, AssetDataService
from .db.mongo_work_service import work_details_service, WorkDetailsService


class MongoService:
    """
    MongoDB 服务兼容类（聚合所有 service 方法）

    注意：这是为了保持向后兼容的封装层
    新代码建议直接使用 services.db 中的具体 service
    """

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_app(self, app):
        """初始化所有 service"""
        asset_data_service.init_app(app)
        work_details_service.init_app(app)

    @property
    def _initialized(self):
        """代理到底层 service 的初始化状态"""
        return hasattr(asset_data_service, '_initialized') and asset_data_service._initialized

    # ========== 以下方法委托给对应的 service ==========

    # --- AssetData 方法 ---
    def insert_asset_data(self, *args, **kwargs):
        return asset_data_service.insert_asset_data(*args, **kwargs)

    def update_asset_data(self, *args, **kwargs):
        return asset_data_service.update_asset_data(*args, **kwargs)

    def fetch_asset_data(self, *args, **kwargs):
        return asset_data_service.fetch_asset_data(*args, **kwargs)

    def fetch_multiple_asset_data(self, *args, **kwargs):
        return asset_data_service.fetch_multiple_asset_data(*args, **kwargs)

    def delete_asset_data(self, *args, **kwargs):
        return asset_data_service.delete_asset_data(*args, **kwargs)

    # --- WorkDetails 方法 ---
    def insert_work_details(self, *args, **kwargs):
        return work_details_service.insert_work_details(*args, **kwargs)

    def update_work_details(self, *args, **kwargs):
        return work_details_service.update_work_details(*args, **kwargs)

    def fetch_work_details(self, *args, **kwargs):
        return work_details_service.fetch_work_details(*args, **kwargs)

    def delete_work_details(self, *args, **kwargs):
        return work_details_service.delete_work_details(*args, **kwargs)

    def add_asset_to_work(self, *args, **kwargs):
        return work_details_service.add_asset_to_work(*args, **kwargs)

    def remove_asset_from_work(self, *args, **kwargs):
        return work_details_service.remove_asset_from_work(*args, **kwargs)

    def add_chapter_to_work(self, *args, **kwargs):
        return work_details_service.add_chapter_to_work(*args, **kwargs)

    def remove_chapter_from_work(self, *args, **kwargs):
        return work_details_service.remove_chapter_from_work(*args, **kwargs)


# 保持单例模式
mongo_service = MongoService()
