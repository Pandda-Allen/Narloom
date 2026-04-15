"""
MongoDB 数据访问层 - AnimeDetails（原 ShotDetails）
负责 anime_details 集合的 CRUD 操作
存放每个 anime 镜头所调用的 asset_id（anime 视频 + 上传的 picture）
"""
import threading
from typing import Optional, Dict, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from services.base_service import BaseService


class AnimeDetailsService(BaseService):
    """AnimeDetails 数据访问类（原 ShotDetailsService）"""

    _instance = None
    _lock = threading.Lock()
    _client = None
    _collection: Optional[Collection] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def init_app(self, app):
        with app.app_context():
            self._initialize()

    def _initialize(self):
        if self._initialized:
            return

        mongo_uri = self._get_config('MONGO_URI')
        mongo_db = self._get_config('MONGO_DB')
        collection_name = self._get_config('MONGO_ANIME_DETAILS_COLLECTION', 'anime_details')

        if not mongo_uri or not mongo_db:
            self._log("MongoDB configuration incomplete", level='error')
            raise RuntimeError("MongoDB configuration incomplete")

        try:
            self._client = MongoClient(mongo_uri)
            db = self._client[mongo_db]
            self._collection = db[collection_name]

            # 创建索引
            self._collection.create_index('anime_id', unique=True)

            # 复合索引
            self._collection.create_index([('anime_id', 1), ('asset_ids', 1)])
            self._collection.create_index([('work_id', 1), ('anime_id', 1)])

            self._initialized = True
        except Exception as e:
            self._log(f"MongoDB initialization error: {str(e)}", level='error')
            raise

    def _ensure_collection(self) -> Collection:
        if self._collection is None:
            self._initialize()
        return self._collection

    def insert_anime_details(self, anime_id: str, work_id: str,
                            asset_ids: List[str] = None,
                            video_assets: List[Dict] = None,
                            picture_assets: List[Dict] = None,
                            extra_data: Dict = None) -> None:
        """插入 anime details 到 MongoDB"""
        collection = self._ensure_collection()
        try:
            doc = {
                'anime_id': anime_id,
                'work_id': work_id,
                'asset_ids': asset_ids or [],
                'video_assets': video_assets or [],
                'picture_assets': picture_assets or []
            }
            if extra_data:
                doc.update(extra_data)
            collection.insert_one(doc)
        except PyMongoError as e:
            self._log(f"MongoDB insert failed for anime {anime_id}: {str(e)}", level='error')
            raise

    def update_anime_details(self, anime_id: str, asset_ids: List[str] = None,
                            video_assets: List[Dict] = None,
                            picture_assets: List[Dict] = None) -> bool:
        """更新 anime details 到 MongoDB"""
        collection = self._ensure_collection()
        update_fields = {}
        if asset_ids is not None:
            update_fields['asset_ids'] = asset_ids
        if video_assets is not None:
            update_fields['video_assets'] = video_assets
        if picture_assets is not None:
            update_fields['picture_assets'] = picture_assets
        if not update_fields:
            return False

        result = collection.update_one(
            {'anime_id': anime_id},
            {'$set': update_fields}
        )
        return result.matched_count > 0

    def fetch_anime_details(self, anime_id: str) -> Optional[Dict]:
        """从 MongoDB 中获取 anime details"""
        collection = self._ensure_collection()
        doc = collection.find_one({'anime_id': anime_id})
        return doc if doc else None

    def fetch_anime_details_by_work(self, work_id: str) -> List[Dict]:
        """根据 work_id 获取所有 anime details"""
        collection = self._ensure_collection()
        docs = collection.find({'work_id': work_id})
        return list(docs) if docs else []

    def delete_anime_details(self, anime_id: str) -> bool:
        """从 MongoDB 中删除 anime details"""
        collection = self._ensure_collection()
        result = collection.delete_one({'anime_id': anime_id})
        return result.deleted_count > 0

    def add_asset_to_anime(self, anime_id: str, asset_id: str,
                          asset_type: str = 'video',
                          asset_data: Dict = None) -> bool:
        """将 asset_id 添加到 anime 的 asset_ids"""
        collection = self._ensure_collection()

        # 构建更新操作
        update_ops = {'$addToSet': {'asset_ids': asset_id}}

        if asset_type == 'video' and asset_data:
            update_ops['$push'] = {'video_assets': asset_data}
        elif asset_type == 'picture' and asset_data:
            update_ops['$push'] = {'picture_assets': asset_data}

        result = collection.update_one(
            {'anime_id': anime_id},
            update_ops
        )
        return result.matched_count > 0

    def remove_asset_from_anime(self, anime_id: str, asset_id: str) -> bool:
        """从 anime 的 asset_ids 中移除 asset_id"""
        collection = self._ensure_collection()
        result = collection.update_one(
            {'anime_id': anime_id},
            {'$pull': {'asset_ids': asset_id}}
        )
        return result.matched_count > 0


anime_details_service = AnimeDetailsService()
