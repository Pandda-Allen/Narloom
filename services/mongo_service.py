"""
MongoDB 服务兼容性封装模块
为保持向后兼容，将所有服务方法聚合到 MongoService 类中

⚠️ 废弃警告 (Deprecated):
    此兼容层已废弃，新代码应直接使用 db 中的具体 service:
    - AssetDataService (asset_data_service) - 资产数据存储
    - WorkDetailsService (work_details_service) - 作品详情
    - NovelDetailsService (novel_details_service) - 小说作品详情
    - AnimeDetailsService (anime_details_service) - 动画作品详情（含镜头详情）

迁移示例:
    # 旧代码
    MongoService().insert_asset_data(asset_id, data)

    # 新代码
    from db import asset_data_service
    asset_data_service.insert_asset_data(asset_id, data)
"""
import logging
from db.mongo_asset import asset_data_service, AssetDataService
from db.mongo_work import work_details_service, WorkDetailsService
from db.mongo_novel import novel_details_service, NovelDetailsService
from db.mongo_anime import anime_details_service, AnimeDetailsService

logger = logging.getLogger(__name__)


def _log_deprecation_warning(method_name: str, target_service: str):
    """记录废弃警告日志"""
    logger.warning(
        f"Deprecated: MongoService.{method_name}() is deprecated. "
        f"Use {target_service} directly instead."
    )


class MongoService:
    """
    MongoDB 服务兼容类（聚合所有 service 方法）

    ⚠️ 废弃警告：此类已废弃，仅保留用于向后兼容
    新代码应直接使用 services.db 中的具体 service
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

    @property
    def _initialized(self):
        """代理到底层 service 的初始化状态"""
        return hasattr(asset_data_service, '_initialized') and asset_data_service._initialized

    # ========== 以下方法委托给对应的 service (已废弃) ==========

    # --- AssetData 方法 ---
    def insert_asset_data(self, *args, **kwargs):
        _log_deprecation_warning('insert_asset_data', 'asset_data_service')
        return asset_data_service.insert_asset_data(*args, **kwargs)

    def update_asset_data(self, *args, **kwargs):
        _log_deprecation_warning('update_asset_data', 'asset_data_service')
        return asset_data_service.update_asset_data(*args, **kwargs)

    def fetch_asset_data(self, *args, **kwargs):
        _log_deprecation_warning('fetch_asset_data', 'asset_data_service')
        return asset_data_service.fetch_asset_data(*args, **kwargs)

    def fetch_multiple_asset_data(self, *args, **kwargs):
        _log_deprecation_warning('fetch_multiple_asset_data', 'asset_data_service')
        return asset_data_service.fetch_multiple_asset_data(*args, **kwargs)

    def delete_asset_data(self, *args, **kwargs):
        _log_deprecation_warning('delete_asset_data', 'asset_data_service')
        return asset_data_service.delete_asset_data(*args, **kwargs)

    # --- WorkDetails 方法 ---
    def insert_work_details(self, *args, **kwargs):
        _log_deprecation_warning('insert_work_details', 'work_details_service')
        return work_details_service.insert_work_details(*args, **kwargs)

    def update_work_details(self, *args, **kwargs):
        _log_deprecation_warning('update_work_details', 'work_details_service')
        return work_details_service.update_work_details(*args, **kwargs)

    def fetch_work_details(self, *args, **kwargs):
        _log_deprecation_warning('fetch_work_details', 'work_details_service')
        return work_details_service.fetch_work_details(*args, **kwargs)

    def delete_work_details(self, *args, **kwargs):
        _log_deprecation_warning('delete_work_details', 'work_details_service')
        return work_details_service.delete_work_details(*args, **kwargs)

    def add_asset_to_work(self, *args, **kwargs):
        _log_deprecation_warning('add_asset_to_work', 'work_details_service')
        return work_details_service.add_asset_to_work(*args, **kwargs)

    def remove_asset_from_work(self, *args, **kwargs):
        _log_deprecation_warning('remove_asset_from_work', 'work_details_service')
        return work_details_service.remove_asset_from_work(*args, **kwargs)

    def add_chapter_to_work(self, *args, **kwargs):
        _log_deprecation_warning('add_chapter_to_work', 'work_details_service')
        return work_details_service.add_chapter_to_work(*args, **kwargs)

    def remove_chapter_from_work(self, *args, **kwargs):
        _log_deprecation_warning('remove_chapter_from_work', 'work_details_service')
        return work_details_service.remove_chapter_from_work(*args, **kwargs)

    # --- NovelDetails 方法 ---
    def insert_novel_details(self, *args, **kwargs):
        _log_deprecation_warning('insert_novel_details', 'novel_details_service')
        return novel_details_service.insert_novel_details(*args, **kwargs)

    def update_novel_details(self, *args, **kwargs):
        _log_deprecation_warning('update_novel_details', 'novel_details_service')
        return novel_details_service.update_novel_details(*args, **kwargs)

    def fetch_novel_details(self, *args, **kwargs):
        _log_deprecation_warning('fetch_novel_details', 'novel_details_service')
        return novel_details_service.fetch_novel_details(*args, **kwargs)

    def delete_novel_details(self, *args, **kwargs):
        _log_deprecation_warning('delete_novel_details', 'novel_details_service')
        return novel_details_service.delete_novel_details(*args, **kwargs)

    def add_asset_to_novel(self, *args, **kwargs):
        _log_deprecation_warning('add_asset_to_novel', 'novel_details_service')
        return novel_details_service.add_asset_to_novel(*args, **kwargs)

    def remove_asset_from_novel(self, *args, **kwargs):
        _log_deprecation_warning('remove_asset_from_novel', 'novel_details_service')
        return novel_details_service.remove_asset_from_novel(*args, **kwargs)

    def add_chapter_to_novel(self, *args, **kwargs):
        _log_deprecation_warning('add_chapter_to_novel', 'novel_details_service')
        return novel_details_service.add_chapter_to_novel(*args, **kwargs)

    def remove_chapter_from_novel(self, *args, **kwargs):
        _log_deprecation_warning('remove_chapter_from_novel', 'novel_details_service')
        return novel_details_service.remove_chapter_from_novel(*args, **kwargs)

    # --- AnimeDetails 方法（含原 ShotDetails）---
    def insert_anime_details(self, *args, **kwargs):
        _log_deprecation_warning('insert_anime_details', 'anime_details_service')
        return anime_details_service.insert_anime_details(*args, **kwargs)

    def update_anime_details(self, *args, **kwargs):
        _log_deprecation_warning('update_anime_details', 'anime_details_service')
        return anime_details_service.update_anime_details(*args, **kwargs)

    def fetch_anime_details(self, *args, **kwargs):
        _log_deprecation_warning('fetch_anime_details', 'anime_details_service')
        return anime_details_service.fetch_anime_details(*args, **kwargs)

    def fetch_anime_details_by_work(self, *args, **kwargs):
        _log_deprecation_warning('fetch_anime_details_by_work', 'anime_details_service')
        return anime_details_service.fetch_anime_details_by_work(*args, **kwargs)

    def delete_anime_details(self, *args, **kwargs):
        _log_deprecation_warning('delete_anime_details', 'anime_details_service')
        return anime_details_service.delete_anime_details(*args, **kwargs)

    def add_asset_to_anime(self, *args, **kwargs):
        _log_deprecation_warning('add_asset_to_anime', 'anime_details_service')
        return anime_details_service.add_asset_to_anime(*args, **kwargs)

    def remove_asset_from_anime(self, *args, **kwargs):
        _log_deprecation_warning('remove_asset_from_anime', 'anime_details_service')
        return anime_details_service.remove_asset_from_anime(*args, **kwargs)

    # --- ShotDetails 方法（已废弃，由 anime_details_service 接管）---
    # 注意：原 shot_details_service 已废弃，所有镜头相关操作由 anime_details_service 处理
    # 原方法已删除，请使用 anime_details_service


# 保持单例模式
mongo_service = MongoService()
