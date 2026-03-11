import os
import logging
from typing import Optional, Dict, Any, List
from flask import current_app
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

class MongoService:
    """MongoDB 服务类（单例），负责 asset_data 集合的操作"""

    _instance = None
    _client = None
    _collection: Optional[Collection] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    # --------- 初始化 ----------
    def init_app(self, app):
        with app.app_context():
            self._initialize()

    def _initialize(self):
        if self._initialized:
            return
        
        mongo_uri = self._get_config('MONGO_URI')
        mongo_db = self._get_config('MONGO_DB')
        mongo_collection = self._get_config('MONGO_COLLECTION', 'asset_data')

        if not mongo_uri or not mongo_db:
            self._log("MongoDB configuration incomplete", level='error')
            raise RuntimeError("MongoDB configuration incomplete")
        
        try:
            self._client = MongoClient(mongo_uri)
            self._collection = self._client[mongo_db][mongo_collection]
            # 创建aset_id唯一索引
            self._collection.create_index('asset_id', unique=True)
            self._initialized = True
            self._log("MongoDB service initialized successfully")
        except Exception as e:
            self._log(f"MongoDB initialization error: {str(e)}", level='error')
            raise

    def _get_config(self, key: str, default=None) -> Optional[str]:
        try:
            if current_app:
                value = current_app.config.get(key, default)
                if value:
                    return value
        except RuntimeError:
            # current_app 不可用
            pass
        return os.getenv(key, default)
    
    def _log(self, message: str, level: str = 'info'):
        try:
            if current_app:
                logger = current_app.logger
                getattr(logger, level)(message)
                return
        except (RuntimeError, AttributeError):
            pass
        logging.basicConfig(level=logging.INFO)
        getattr(logging, level)(message)

    def _ensure_collection(self) -> Collection:
        if not self._collection:
            self._initialize()
        return self._collection
    
    # --------- 数据操作 ----------
    def insert_asset_data(self, asset_id: str, asset_data: Dict = None) -> None:
        """插入 asset_data 到 MongoDB"""
        collection = self._ensure_collection()
        print(f"Inserting asset_data for asset_id {asset_id} into MongoDB")
        print(f"Asset data: {asset_data}")
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

mongo_service = MongoService()