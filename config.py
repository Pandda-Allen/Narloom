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
    cors_origins_str = os.getenv('CORS_ORIGINS', '*')
    CORS_ORIGINS = ['*'] if cors_origins_str == '' else cors_origins_str.split(',')
    
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

    # MySQL配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'narloom')
    MYSQL_TABLE_ASSETS = os.getenv('MYSQL_TABLE_ASSETS', 'assets')
    MYSQL_TABLE_WORKS = os.getenv('MYSQL_TABLE_WORKS', 'works')
    MYSQL_TABLE_CHAPTERS = os.getenv('MYSQL_TABLE_CHAPTERS', 'chapters')
    MYSQL_TABLE_USERS = os.getenv('MYSQL_TABLE_USERS', 'users')
    MYSQL_CHARSET = os.getenv('MYSQL_CHARSET', 'utf8mb4')

    # Mongodb配置
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB = os.getenv('MONGO_DB', 'narloom')
    MONGO_ASSET_DATA_COLLECTION = os.getenv('MONGO_ASSET_DATA_COLLECTION', 'asset_data')
    MONGO_WORK_DETAILS_COLLECTION = os.getenv('MONGO_WORK_DETAILS_COLLECTION', 'work_details')
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保上传目录存在（本地备用）
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('logs', exist_ok=True)