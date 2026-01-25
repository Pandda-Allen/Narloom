import os
from dotenv import load_dotenv
from datetime import timedelta

# 载入环境变量
load_dotenv()

class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # Supabase 配置
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
    
    # API 配置
    API_PREFIX = 'http://120.26.103.23'

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保上传目录存在（本地备用）
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('logs', exist_ok=True)