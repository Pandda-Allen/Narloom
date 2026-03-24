"""
MongoDB 数据访问层 - WorkDetails
负责 work_details 集合的 CRUD 操作
"""
import threading
from typing import Optional, Dict, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from ..base_service import BaseService


class WorkDetailsService(BaseService):
    """WorkDetails 数据访问类"""

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
        collection_name = self._get_config('MONGO_WORK_DETAILS_COLLECTION')

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
            self._collection.create_index([('work_id', 1), ('asset_ids', 1)])

            self._collection.create_index([('work_id', 1), ('chapter_ids', 1)])

            self._initialized = True
        except Exception as e:
            self._log(f"MongoDB initialization error: {str(e)}", level='error')
            raise

    def _ensure_collection(self) -> Collection:
        if self._collection is None:
            self._initialize()
        return self._collection

    def insert_work_details(self, work_id: str, asset_ids: List[str] = None,
                            chapter_ids: List[str] = None) -> None:
        """插入 work details 到 MongoDB"""
        collection = self._ensure_collection()
        try:
            collection.insert_one({
                'work_id': work_id,
                'asset_ids': asset_ids or [],
                'chapter_ids': chapter_ids or []
            })
        except PyMongoError as e:
            self._log(f"MongoDB insert failed for work {work_id}: {str(e)}", level='error')
            raise

    def update_work_details(self, work_id: str, asset_ids: List[str] = None,
                            chapter_ids: List[str] = None) -> bool:
        """更新 work details 到 MongoDB"""
        collection = self._ensure_collection()
        update_fields = {}
        if asset_ids is not None:
            update_fields['asset_ids'] = asset_ids
        if chapter_ids is not None:
            update_fields['chapter_ids'] = chapter_ids
        if not update_fields:
            return False

        result = collection.update_one(
            {'work_id': work_id},
            {'$set': update_fields}
        )
        return result.matched_count > 0

    def fetch_work_details(self, work_id: str) -> Optional[Dict]:
        """从 MongoDB 中获取 work details"""
        collection = self._ensure_collection()
        doc = collection.find_one({'work_id': work_id})
        return doc if doc else None

    def delete_work_details(self, work_id: str) -> bool:
        """从 MongoDB 中删除 work details"""
        collection = self._ensure_collection()
        result = collection.delete_one({'work_id': work_id})
        return result.deleted_count > 0

    def add_asset_to_work(self, work_id: str, asset_id: str) -> bool:
        """将 asset_id 添加到 work 的 asset_ids"""
        collection = self._ensure_collection()
        result = collection.update_one(
            {'work_id': work_id},
            {'$addToSet': {'asset_ids': asset_id}}
        )
        return result.matched_count > 0

    def remove_asset_from_work(self, work_id: str, asset_id: str) -> bool:
        """从 work 的 asset_ids 中移除 asset_id"""
        collection = self._ensure_collection()
        result = collection.update_one(
            {'work_id': work_id},
            {'$pull': {'asset_ids': asset_id}}
        )
        return result.matched_count > 0

    def add_chapter_to_work(self, work_id: str, chapter_id: str) -> bool:
        """将 chapter_id 添加到 work 的 chapter_ids"""
        collection = self._ensure_collection()
        result = collection.update_one(
            {'work_id': work_id},
            {'$addToSet': {'chapter_ids': chapter_id}}
        )
        return result.matched_count > 0

    def remove_chapter_from_work(self, work_id: str, chapter_id: str) -> bool:
        """从 work 的 chapter_ids 中移除 chapter_id"""
        collection = self._ensure_collection()
        result = collection.update_one(
            {'work_id': work_id},
            {'$pull': {'chapter_ids': chapter_id}}
        )
        return result.matched_count > 0


work_details_service = WorkDetailsService()
