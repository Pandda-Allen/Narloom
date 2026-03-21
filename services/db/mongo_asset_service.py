"""
MongoDB 数据访问层 - AssetData
负责 asset_data 集合的 CRUD 操作
"""
import threading
from typing import Optional, Dict, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from ..base_service import BaseService


class AssetDataService(BaseService):
    """AssetData 数据访问类"""

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
        collection_name = self._get_config('MONGO_ASSET_DATA_COLLECTION')

        if not mongo_uri or not mongo_db:
            self._log("MongoDB configuration incomplete", level='error')
            raise RuntimeError("MongoDB configuration incomplete")

        try:
            self._client = MongoClient(mongo_uri)
            db = self._client[mongo_db]
            self._collection = db[collection_name]

            # 创建索引
            self._collection.create_index('asset_id', unique=True)
            self._log(f"Created index: {collection_name}.asset_id (unique)")

            self._initialized = True
            self._log("AssetData service initialized successfully")
        except Exception as e:
            self._log(f"MongoDB initialization error: {str(e)}", level='error')
            raise

    def _ensure_collection(self) -> Collection:
        if self._collection is None:
            self._initialize()
        return self._collection

    def insert_asset_data(self, asset_id: str, asset_data: Dict = None) -> None:
        """插入 asset_data 到 MongoDB"""
        collection = self._ensure_collection()
        try:
            collection.insert_one({
                'asset_id': asset_id,
                'asset_data': asset_data or {},
            })
        except PyMongoError as e:
            self._log(f"MongoDB insert failed for asset {asset_id}: {str(e)}", level='error')
            raise

    def update_asset_data(self, asset_id: str, asset_data: Dict) -> bool:
        """更新 asset_data 到 MongoDB"""
        collection = self._ensure_collection()
        result = collection.update_one(
            {'asset_id': asset_id},
            {'$set': {'asset_data': asset_data}}
        )
        return result.matched_count > 0

    def fetch_asset_data(self, asset_id: str) -> Optional[Dict]:
        """从 MongoDB 中获取 asset_data"""
        collection = self._ensure_collection()
        doc = collection.find_one({'asset_id': asset_id})
        return doc['asset_data'] if doc else None

    def fetch_multiple_asset_data(self, asset_ids: List[str]) -> Dict[str, Dict]:
        """批量获取多个 asset_id 的 asset_data"""
        collection = self._ensure_collection()
        cursor = collection.find({'asset_id': {'$in': asset_ids}})
        return {doc['asset_id']: doc['asset_data'] for doc in cursor}

    def delete_asset_data(self, asset_id: str) -> bool:
        """从 MongoDB 中删除 asset_data"""
        collection = self._ensure_collection()
        result = collection.delete_one({'asset_id': asset_id})
        return result.deleted_count > 0


asset_data_service = AssetDataService()
