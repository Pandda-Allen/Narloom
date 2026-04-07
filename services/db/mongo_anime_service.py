"""
MongoDB 数据访问层 - AnimeDetails
负责 anime_details 集合的 CRUD 操作
主要记录 shots_id 列表
"""
import threading
from typing import Optional, Dict, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from ..base_service import BaseService


class AnimeDetailsService(BaseService):
    """AnimeDetails 数据访问类"""

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
            self._collection.create_index('work_id', unique=True)

            # 复合索引
            self._collection.create_index([('work_id', 1), ('shots_ids', 1)])

            self._initialized = True
        except Exception as e:
            self._log(f"MongoDB initialization error: {str(e)}", level='error')
            raise

    def _ensure_collection(self) -> Collection:
        if self._collection is None:
            self._initialize()
        return self._collection

    def insert_anime_details(self, work_id: str, shots_ids: List[str] = None,
                             extra_data: Dict = None) -> None:
        """插入 anime details 到 MongoDB"""
        collection = self._ensure_collection()
        try:
            doc = {
                'work_id': work_id,
                'shots_ids': shots_ids or []
            }
            if extra_data:
                doc.update(extra_data)
            collection.insert_one(doc)
        except PyMongoError as e:
            self._log(f"MongoDB insert failed for work {work_id}: {str(e)}", level='error')
            raise

    def update_anime_details(self, work_id: str, shots_ids: List[str] = None) -> bool:
        """更新 anime details 到 MongoDB"""
        collection = self._ensure_collection()
        update_fields = {}
        if shots_ids is not None:
            update_fields['shots_ids'] = shots_ids
        if not update_fields:
            return False

        result = collection.update_one(
            {'work_id': work_id},
            {'$set': update_fields}
        )
        return result.matched_count > 0

    def fetch_anime_details(self, work_id: str) -> Optional[Dict]:
        """从 MongoDB 中获取 anime details"""
        collection = self._ensure_collection()
        doc = collection.find_one({'work_id': work_id})
        return doc if doc else None

    def delete_anime_details(self, work_id: str) -> bool:
        """从 MongoDB 中删除 anime details"""
        collection = self._ensure_collection()
        result = collection.delete_one({'work_id': work_id})
        return result.deleted_count > 0

    def add_shot_to_anime(self, work_id: str, shot_id: str) -> bool:
        """将 shot_id 添加到 anime 的 shots_ids"""
        collection = self._ensure_collection()
        result = collection.update_one(
            {'work_id': work_id},
            {'$addToSet': {'shots_ids': shot_id}}
        )
        return result.matched_count > 0

    def remove_shot_from_anime(self, work_id: str, shot_id: str) -> bool:
        """从 anime 的 shots_ids 中移除 shot_id"""
        collection = self._ensure_collection()
        result = collection.update_one(
            {'work_id': work_id},
            {'$pull': {'shots_ids': shot_id}}
        )
        return result.matched_count > 0


anime_details_service = AnimeDetailsService()
