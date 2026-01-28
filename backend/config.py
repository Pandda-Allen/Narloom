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

    # AI模型配置
    AI_MODEL_TYPE = os.getenv('AI_MODEL_TYPE', 'openai') #可选： openai，claude，local
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保上传目录存在（本地备用）
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('logs', exist_ok=True)