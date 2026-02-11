# services/supabase_service.py
import os
import logging
from typing import Optional, Dict, Any, Union
from supabase import create_client, Client
from flask import current_app

class SupabaseService:
    """Supabase 服务类（单例），提供所有数据库操作的统一入口"""

    _instance = None
    _client: Optional[Client] = None
    _initialized = False

    # ---------- 表名映射 ----------
    _TABLES = {
        'character': 'character_asset',
        'world': 'world_asset',
        'novel': 'novel_work',
        'chapter': 'novel_chapter',
        'map': 'work_asset_map',
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ---------- 初始化 ----------
    def init_app(self, app):
        with app.app_context():
            self._initialize()

    def _initialize(self):
        """初始化 Supabase 客户端（线程安全）"""
        if self._initialized:
            return

        # 获取配置
        supabase_url = self._get_config('SUPABASE_URL')
        supabase_key = self._get_config('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            self._log("Supabase URL or Key not provided. Please check your configuration.", level='warning')
            return

        try:
            self._client = create_client(supabase_url, supabase_key)
            self._initialized = True
            self._log("Supabase client initialized successfully")
        except Exception as e:
            self._client = None
            self._initialized = False
            self._log(f"Error initializing Supabase client: {e}", level='error')

    def _get_config(self, key: str) -> Optional[str]:
        """从 Flask 配置或环境变量获取配置值"""
        try:
            if current_app:
                value = current_app.config.get(key)
                if value:
                    return value
        except RuntimeError:
            pass
        return os.getenv(key)

    def _log(self, message: str, level: str = 'info'):
        """统一日志输出，兼容 Flask 和非 Flask 环境"""
        try:
            if current_app:
                logger = current_app.logger
                getattr(logger, level)(message)
                return
        except (RuntimeError, AttributeError):
            pass

        # 回退到标准 logging
        logging.basicConfig(level=logging.INFO)
        getattr(logging, level)(message)

    # ---------- 客户端保证 ----------
    def _ensure_client(self) -> Client:
        """确保客户端已初始化，否则抛出异常"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise RuntimeError("Supabase client is not initialized. Call init_app() first.")
        return self._client

    # ---------- 通用数据库操作 ----------
    def _table(self, table_key: str):
        """根据表键获取 Supabase 表对象"""
        table_name = self._TABLES.get(table_key)
        if not table_name:
            raise ValueError(f"Unknown table key: {table_key}")
        return self._ensure_client().table(table_name)

    def _execute(self, operation, *args, **kwargs):
        """统一执行数据库操作并处理异常"""
        try:
            return operation(*args, **kwargs).execute()
        except Exception as e:
            self._log(f"Database operation failed: {e}", level='error')
            raise

    # ---------- Asset 操作（多表）----------
    def asset_insert(self, asset_data: Dict, asset_type: str):
        """插入资产（character/world）"""
        return self._execute(self._table(asset_type).insert, asset_data)

    def asset_update(self, asset_id: str, asset_data: Dict, asset_type: str):
        """更新资产"""
        return self._execute(
            self._table(asset_type).update(asset_data).eq, 'asset_id', asset_id
        )

    def asset_fetch_by_id(self, asset_id: str, asset_type: str):
        """根据 ID 获取单个资产"""
        return self._execute(self._table(asset_type).select('*').eq, 'asset_id', asset_id)

    def asset_fetch_all(self, asset_type: Optional[str], user_id: str,
                        limit: int = 100, offset: int = 0) -> Dict[str, list]:
        """
        获取用户的资产列表，支持按类型筛选
        返回统一格式: {'data': [...]}
        """
        if asset_type in ('character', 'world'):
            resp = self._execute(
                self._table(asset_type).select('*').eq('user_id', user_id).limit(limit).offset,
                offset
            )
            return {'data': resp.data}
        else:
            # 获取全部类型
            char_resp = self._execute(
                self._table('character').select('*').eq('user_id', user_id)
            )
            world_resp = self._execute(
                self._table('world').select('*').eq('user_id', user_id)
            )
            return {'data': char_resp.data + world_resp.data}

    def asset_delete(self, asset_id: str, asset_type: str):
        """删除资产"""
        if asset_type not in ('character', 'world'):
            raise ValueError("Invalid asset type for deletion. Must be 'character' or 'world'")
        return self._execute(self._table(asset_type).delete().eq, 'asset_id', asset_id)

    # ---------- Novel 操作 ----------
    def novel_create(self, novel_data: Dict):
        return self._execute(self._table('novel').insert, novel_data)

    def novel_update(self, novel_id: str, novel_data: Dict):
        return self._execute(self._table('novel').update(novel_data).eq, 'novel_id', novel_id)

    def novel_fetch_by_id(self, novel_id: str):
        return self._execute(self._table('novel').select('*').eq, 'novel_id', novel_id)

    def novel_fetch_by_author_id(self, author_id: str):
        return self._execute(self._table('novel').select('*').eq, 'author_id', author_id)

    # ---------- Chapter 操作 ----------
    def chapter_create(self, chapter_data: Dict):
        return self._execute(self._table('chapter').insert, chapter_data)

    def chapter_update(self, chapter_id: str, chapter_data: Dict):
        return self._execute(self._table('chapter').update(chapter_data).eq, 'chapter_id', chapter_id)

    def chapter_fetch_by_novel_id(self, novel_id: str):
        return self._execute(self._table('chapter').select('*').eq, 'novel_id', novel_id)

    # ---------- Work-Asset Map 操作 ----------
    def map_insert(self, map_data: Dict):
        return self._execute(self._table('map').insert, map_data)

    def map_fetch_by_ids(self, work_id: str, user_id: str):
        return self._execute(
            self._table('map').select('*').eq('work_id', work_id).eq, 'user_id', user_id
        )

    def map_delete(self, asset_id: str, work_id: str, user_id: str):
        return self._execute(
            self._table('map').delete()
            .eq('asset_id', asset_id)
            .eq('work_id', work_id)
            .eq, 'user_id', user_id
        )

    # ---------- 认证 ----------
    def login(self, email: str, password: str):
        """用户密码登录"""
        try:
            response = self._ensure_client().auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            self._log(f"User {email} logged in successfully")
            return response
        except Exception as e:
            self._log(f"Login failed for {email}: {e}", level='warning')
            raise

    # ---------- 属性 ----------
    @property
    def client(self) -> Optional[Client]:
        """获取原始 Supabase 客户端（谨慎使用）"""
        return self._ensure_client() if self._initialized else None


# 全局单例实例
supabase_service = SupabaseService()