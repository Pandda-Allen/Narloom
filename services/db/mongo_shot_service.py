"""
MongoDB 数据访问层 - ShotDetails
负责 shot_details 集合的 CRUD 操作
存放每个 shot 所调用的 asset_id（anime 视频 + 上传的 picture）
"""
import threading
from typing import Optional, Dict, List
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from ..base_service import BaseService


class ShotDetailsService(BaseService):
    """ShotDetails 数据访问类"""

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
        collection_name = self._get_config('MONGO_SHOT_DETAILS_COLLECTION', 'shot_details')

        if not mongo_uri or not mongo_db:
            self._log("MongoDB configuration incomplete", level='error')
            raise RuntimeError("MongoDB configuration incomplete")

        try:
            self._client = MongoClient(mongo_uri)
            db = self._client[mongo_db]
            self._collection = db[collection_name]

            # 创建索引
            self._collection.create_index('shot_id', unique=True)

            # 复合索引
            self._collection.create_index([('shot_id', 1), ('asset_ids', 1)])

            self._collection.create_index([('work_id', 1), ('shot_id', 1)])

            self._initialized = True
        except Exception as e:
            self._log(f"MongoDB initialization error: {str(e)}", level='error')
            raise

    def _ensure_collection(self) -> Collection:
        if self._collection is None:
            self._initialize()
        return self._collection

    def insert_shot_details(self, shot_id: str, work_id: str,
                            asset_ids: List[str] = None,
                            video_assets: List[Dict] = None,
                            picture_assets: List[Dict] = None,
                            extra_data: Dict = None) -> None:
        """插入 shot details 到 MongoDB"""
        collection = self._ensure_collection()
        try:
            doc = {
                'shot_id': shot_id,
                'work_id': work_id,
                'asset_ids': asset_ids or [],
                'video_assets': video_assets or [],
                'picture_assets': picture_assets or []
            }
            if extra_data:
                doc.update(extra_data)
            collection.insert_one(doc)
        except PyMongoError as e:
            self._log(f"MongoDB insert failed for shot {shot_id}: {str(e)}", level='error')
            raise

    def update_shot_details(self, shot_id: str, asset_ids: List[str] = None,
                            video_assets: List[Dict] = None,
                            picture_assets: List[Dict] = None) -> bool:
        """更新 shot details 到 MongoDB"""
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
            {'shot_id': shot_id},
            {'$set': update_fields}
        )
        return result.matched_count > 0

    def fetch_shot_details(self, shot_id: str) -> Optional[Dict]:
        """从 MongoDB 中获取 shot details"""
        collection = self._ensure_collection()
        doc = collection.find_one({'shot_id': shot_id})
        return doc if doc else None

    def fetch_shot_details_by_work(self, work_id: str) -> List[Dict]:
        """根据 work_id 获取所有 shot details"""
        collection = self._ensure_collection()
        docs = collection.find({'work_id': work_id})
        return list(docs) if docs else []

    def delete_shot_details(self, shot_id: str) -> bool:
        """从 MongoDB 中删除 shot details"""
        collection = self._ensure_collection()
        result = collection.delete_one({'shot_id': shot_id})
        return result.deleted_count > 0

    def add_asset_to_shot(self, shot_id: str, asset_id: str,
                          asset_type: str = 'video',
                          asset_data: Dict = None) -> bool:
        """将 asset_id 添加到 shot 的 asset_ids"""
        collection = self._ensure_collection()

        update_data = {}
        if asset_type == 'video':
            update_data = {'$addToSet': {'video_assets': asset_data or {'asset_id': asset_id}}}
        elif asset_type == 'picture':
            update_data = {'$addToSet': {'picture_assets': asset_data or {'asset_id': asset_id}}}

        result = collection.update_one(
            {'shot_id': shot_id},
            {'$addToSet': {'asset_ids': asset_id}},
            **update_data
        )
        return result.matched_count > 0

    def remove_asset_from_shot(self, shot_id: str, asset_id: str) -> bool:
        """从 shot 的 asset_ids 中移除 asset_id"""
        collection = self._ensure_collection()
        result = collection.update_one(
            {'shot_id': shot_id},
            {'$pull': {'asset_ids': asset_id}}
        )
        return result.matched_count > 0


shot_details_service = ShotDetailsService()
