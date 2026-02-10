import os
from supabase import create_client, Client
from flask import current_app
from typing import Optional, Any

class SupabaseService:
    """Supabase service class"""

    _instance = None
    _client: Optional[Client] = None
    _initialized = False # 添加初始化状态标识栏

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
        return cls._instance
    
    def init_app(self, app):
        with app.app_context():
            self._initialize()
    def _initialize(self):
        '''Supabase 初始化'''
        supabase_url = None
        supabase_key = None

        # 尝试从当前应用中获取配置
        try:
            if current_app:
                supabase_url = current_app.config.get('SUPABASE_URL')
                supabase_key = current_app.config.get('SUPABASE_KEY')
        except RuntimeError:
            # current_app 不可用
            pass

        # 如果当前应用配置中没有，则从环境变量（.env）中获取
        if not supabase_url or not supabase_key:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')

        if supabase_url and supabase_key:
            try:
                self._client = create_client(supabase_url, supabase_key)
                self._initialized = True
                try:
                    if current_app:
                        current_app.logger.info("Supabase client initialized successfully")
                    else:
                        print("Supabase client initialized successfully")
                except:
                    print("Supabase client initialized successfully")
                current_app.logger.info("Supabase client initialized successfully")
            except Exception as e:
                self._client = None
                self._initialized = False

                try:
                    if current_app:
                        current_app.logger.error(f"Error initializing Supabase client: {e}")
                    else:
                        print(f"Error initializing Supabase client: {e}")
                except:
                    print(f"Error initializing Supabase client: {e}")
        else:
            print("Supabase URL or Key not provided. Please check your configuration.")

    def client_login(self, email: str, password: str):
        """User login using Supabase auth"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            response = self._client.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            return response
        except Exception as e:
            raise e

    ## asset数据库(character_asset, world_asset)操作 ##
    def asset_insert(self, asset_data, asset_type):
        """Insert an asset into Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            if asset_type == 'character':
                response = self._client.table('character_asset').insert(asset_data).execute()
            elif asset_type == 'world':
                response = self._client.table('world_asset').insert(asset_data).execute()
            return response
        except Exception as e:
            raise e

    def asset_update(self, asset_id, asset_data, asset_type):
        """Update an asset in Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            if asset_type == 'character':
                response = self._client.table('character_asset').update(asset_data).eq('asset_id', asset_id).execute()
            elif asset_type == 'world':
                response = self._client.table('world_asset').update(asset_data).eq('asset_id', asset_id).execute()
            return response
        except Exception as e:
            raise e

    def asset_fetch_by_id(self, asset_id, asset_type):
        """Fetch an asset by ID from Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            if asset_type == 'character':
                response = self._client.table('character_asset').select('*').eq('asset_id', asset_id).execute()
            elif asset_type == 'world':
                response = self._client.table('world_asset').select('*').eq('asset_id', asset_id).execute()
            return response
        except Exception as e:
            raise e
        
    def asset_fetch_all(self, asset_type=None, user_id=None, limit=100, offset=0):
        """Fetch all assets from Supabase, with optional filtering"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            if asset_type == 'character':
                query = self._client.table('character_asset').select('*').eq('user_id', user_id)
            elif asset_type == 'world':
                query = self._client.table('world_asset').select('*').eq('user_id', user_id)
            else:
                # 如果没有指定类型，则获取所有类型的资产
                char_query = self._client.table('character_asset').select('*').eq('user_id', user_id)
                world_query = self._client.table('world_asset').select('*').eq('user_id', user_id)
                char_response = char_query.execute()
                world_response = world_query.execute()
                combined_data = char_response.data + world_response.data
                return {'data': combined_data}

            query = query.limit(limit).offset(offset)
            response = query.execute()
            return response
        except Exception as e:
            raise e

    def asset_delete(self, asset_id, asset_type):
        """Delete an asset from Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            if asset_type == 'character':
                response = self._client.table('character_asset').delete().eq('asset_id', asset_id).execute()
            elif asset_type == 'world':
                response = self._client.table('world_asset').delete().eq('asset_id', asset_id).execute()
            else:
                raise ValueError("Invalid asset type specified for deletion.")
            return response
        except Exception as e:
            raise e

    ##  work数据库(novel_work)操作 ##
    def novel_create(self, novel_data):
        """Create a new novel work in Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            response = self._client.table('novel_work').insert(novel_data).execute()
            return response
        except Exception as e:
            raise e

    def novel_update(self, novel_id, novel_data):
        """Update an existing novel work in Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            response = self._client.table('novel_work').update(novel_data).eq('novel_id', novel_id).execute()
            return response
        except Exception as e:
            raise e

    def novel_get_by_id(self, novel_id):
        """Fetch a novel work by ID from Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            response = self._client.table('novel_work').select('*').eq('novel_id', novel_id).execute()
            return response
        except Exception as e:
            raise e

    ## work_asset_map数据库操作 ##
    def map_insert(self, map_data):
        """Insert a new mapping into Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            response = self._client.table('work_asset_map').insert(map_data).execute()
            return response
        except Exception as e:
            raise e
    
    def map_fetch_by_ids(self, work_id, user_id):
        """Fetch a mapping by asset_id, work_id and user_id from Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            response = self._client.table('work_asset_map').select('*').eq('work_id', work_id).eq('user_id', user_id).execute()
            return response
        except Exception as e:
            raise e

    def map_delete(self, asset_id, work_id, user_id):
        """Delete a mapping from Supabase"""
        if not self._client:
            self._initialize()
        if not self._client:
            raise Exception("Supabase client is not initialized.")
        
        try:
            response = self._client.table('work_asset_map').delete().eq('asset_id', asset_id).eq('work_id', work_id).eq('user_id', user_id).execute()
            return response
        except Exception as e:
            raise e

    @property
    def client(self) -> Optional[Client]:
        """Get the Supabase client"""
        if not self._client:
            self._initialize()
        return self._client
    
# 全局实例
supabase_service = SupabaseService()