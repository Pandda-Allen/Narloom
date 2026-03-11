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
    _asset_data_collection: Optional[Collection] = None
    _work_details_collection: Optional[Collection] = None
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
        asset_collection = self._get_config('MONGO_ASSET_DATA_COLLECTION')
        work_details_collection = self._get_config('MONGO_WORK_DETAILS_COLLECTION')

        if not mongo_uri or not mongo_db:
            self._log("MongoDB configuration incomplete", level='error')
            raise RuntimeError("MongoDB configuration incomplete")
        
        try:
            self._client = MongoClient(mongo_uri)
            db = self._client[mongo_db]
            self._asset_data_collection = db[asset_collection]
            self._work_details_collection = db[work_details_collection]
            # 创建索引
            self._asset_data_collection.create_index('asset_id', unique=True)
            self._work_details_collection.create_index('work_id', unique=True)
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
        if not self._asset_data_collection:
            self._initialize()
        return self._asset_data_collection
    
    # --------- asset_data 数据操作 ----------
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

    # --------- work details 数据操作 ----------
    def insert_work_details(self, work_id: str, asset_ids: List[str] = None, chapter_ids: List[str] = None) -> None:
        """插入 work details 到 MongoDB"""
        collection = self._work_details_collection
        try:
            collection.insert_one({
                'work_id': work_id,
                'asset_ids': asset_ids or [],
                'chapter_ids': chapter_ids or []
            })
        except PyMongoError as e:
            self._log(f"MongoDB insert failed for work {work_id}: {str(e)}", level='error')
            raise
    
    def update_work_details(self, work_id: str, asset_ids: List[str] = None, chapter_ids: List[str] = None) -> bool:
        """更新 work details 到 MongoDB"""
        collection = self._work_details_collection
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
        collection = self._work_details_collection
        doc = collection.find_one({'work_id': work_id})
        return doc if doc else None

    def delete_work_details(self, work_id: str) -> bool:
        """从 MongoDB 中删除 work details"""
        collection = self._work_details_collection
        result = collection.delete_one({'work_id': work_id})
        return result.deleted_count > 0
    
    def add_asset_to_work(self, work_id: str, asset_id: str) -> bool:
        """将 asset_id 添加到 work 的 asset_ids"""
        collection = self._work_details_collection
        result = collection.update_one(
            {'work_id': work_id},
            {'$addToSet': {'asset_ids': asset_id}}
        )
        return result.matched_count > 0

    def remove_asset_from_work(self, work_id: str, asset_id: str) -> bool:
        """从 work 的 asset_ids 中移除 asset_id"""
        collection = self._work_details_collection
        result = collection.update_one(
            {'work_id': work_id},
            {'$pull': {'asset_ids': asset_id}}
        )
        return result.matched_count > 0
    
    def add_chapter_to_work(self, work_id: str, chapter_id: str) -> bool:
        """将 chapter_id 添加到 work 的 chapter_ids"""
        collection = self._work_details_collection
        result = collection.update_one(
            {'work_id': work_id},
            {'$addToSet': {'chapter_ids': chapter_id}}
        )
        return result.matched_count > 0
    
    def remove_chapter_from_work(self, work_id: str, chapter_id: str) -> bool:
        """从 work 的 chapter_ids 中移除 chapter_id"""
        collection = self._work_details_collection
        result = collection.update_one(
            {'work_id': work_id},
            {'$pull': {'chapter_ids': chapter_id}}
        )
        return result.matched_count > 0


mongo_service = MongoService()