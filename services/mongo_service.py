"""
MongoDB 服务兼容性封装模块
为保持向后兼容，将所有服务方法聚合到 MongoService 类中
新代码建议直接使用 services.db 中的具体 service
"""
from .db.mongo_asset_service import asset_data_service, AssetDataService
from .db.mongo_work_service import work_details_service, WorkDetailsService
from .db.mongo_novel_service import novel_details_service, NovelDetailsService
from .db.mongo_anime_service import anime_details_service, AnimeDetailsService
from .db.mongo_shot_service import shot_details_service, ShotDetailsService


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
        novel_details_service.init_app(app)
        anime_details_service.init_app(app)
        shot_details_service.init_app(app)

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

    # --- NovelDetails 方法 ---
    def insert_novel_details(self, *args, **kwargs):
        return novel_details_service.insert_novel_details(*args, **kwargs)

    def update_novel_details(self, *args, **kwargs):
        return novel_details_service.update_novel_details(*args, **kwargs)

    def fetch_novel_details(self, *args, **kwargs):
        return novel_details_service.fetch_novel_details(*args, **kwargs)

    def delete_novel_details(self, *args, **kwargs):
        return novel_details_service.delete_novel_details(*args, **kwargs)

    def add_asset_to_novel(self, *args, **kwargs):
        return novel_details_service.add_asset_to_novel(*args, **kwargs)

    def remove_asset_from_novel(self, *args, **kwargs):
        return novel_details_service.remove_asset_from_novel(*args, **kwargs)

    def add_chapter_to_novel(self, *args, **kwargs):
        return novel_details_service.add_chapter_to_novel(*args, **kwargs)

    def remove_chapter_from_novel(self, *args, **kwargs):
        return novel_details_service.remove_chapter_from_novel(*args, **kwargs)

    # --- AnimeDetails 方法 ---
    def insert_anime_details(self, *args, **kwargs):
        return anime_details_service.insert_anime_details(*args, **kwargs)

    def update_anime_details(self, *args, **kwargs):
        return anime_details_service.update_anime_details(*args, **kwargs)

    def fetch_anime_details(self, *args, **kwargs):
        return anime_details_service.fetch_anime_details(*args, **kwargs)

    def delete_anime_details(self, *args, **kwargs):
        return anime_details_service.delete_anime_details(*args, **kwargs)

    def add_shot_to_anime(self, *args, **kwargs):
        return anime_details_service.add_shot_to_anime(*args, **kwargs)

    def remove_shot_from_anime(self, *args, **kwargs):
        return anime_details_service.remove_shot_from_anime(*args, **kwargs)

    # --- ShotDetails 方法 ---
    def insert_shot_details(self, *args, **kwargs):
        return shot_details_service.insert_shot_details(*args, **kwargs)

    def update_shot_details(self, *args, **kwargs):
        return shot_details_service.update_shot_details(*args, **kwargs)

    def fetch_shot_details(self, *args, **kwargs):
        return shot_details_service.fetch_shot_details(*args, **kwargs)

    def fetch_shot_details_by_work(self, *args, **kwargs):
        return shot_details_service.fetch_shot_details_by_work(*args, **kwargs)

    def delete_shot_details(self, *args, **kwargs):
        return shot_details_service.delete_shot_details(*args, **kwargs)

    def add_asset_to_shot(self, *args, **kwargs):
        return shot_details_service.add_asset_to_shot(*args, **kwargs)

    def remove_asset_from_shot(self, *args, **kwargs):
        return shot_details_service.remove_asset_from_shot(*args, **kwargs)


# 保持单例模式
mongo_service = MongoService()
