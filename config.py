import os
from dotenv import load_dotenv
from datetime import timedelta

# 载入环境变量
load_dotenv()

class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # API 配置
    API_PREFIX = 'http://120.26.103.23'

    # Supabase 配置
    SUPABASE_URL = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

    # DeepSeek配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_API_BASE = os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com')
    DEEPSEEK_DEFAULT_MODEL = os.getenv('DEEPSEEK_DEFAULT_MODEL', 'deepseek-chat')

    # OpenRouter配置
    # OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    # OPENROUTER_DEFAULT_MODEL = os.getenv('OPENROUTER_DEFAULT_MODEL', 'openai/gpt-3.5-turbo')
    
    # AI服务配置
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', 2000))
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', 0.7))
    AI_REQUEST_TIMEOUT = int(os.getenv('AI_REQUEST_TIMEOUT', 30))
    
    # 会话配置
    SESSION_TIMEOUT = timedelta(hours=2)
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # 速率限制
    RATELIMIT_DEFAULT = "100 per minute"

    # DeepSeek特定配置
    DEEPSEEK_MODELS = {
        'deepseek-chat': {
            'name': 'DeepSeek Chat',
            'description': '通用聊天模型',
            'max_tokens': 4096,
            'context_length': 8192
        },
        'deepseek-coder': {
            'name': 'DeepSeek Coder',
            'description': '代码生成和编程助手',
            'max_tokens': 4096,
            'context_length': 8192
        }
    }
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保上传目录存在（本地备用）
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('logs', exist_ok=True)