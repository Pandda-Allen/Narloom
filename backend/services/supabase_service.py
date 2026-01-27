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

    @property
    def client(self) -> Optional[Client]:
        """Get the Supabase client"""
        if not self._client:
            self._initialize()
        return self._client

    def login(self, email, password):
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            # 登录成功后的用户信息
            user = response.user
            session = response.session

            print(f"登录成功！用户ID: {user}")
            print(f"访问令牌: {session}")
            print(f"刷新令牌: {session.refresh_token}")
        except Exception as e:
            print(e)
    
# 全局实例
supabase_service = SupabaseService()