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

    # 阿里云 DashScope（通义千问）配置
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
    DASHSCOPE_API_BASE = os.getenv('DASHSCOPE_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    DASHSCOPE_DEFAULT_MODEL = os.getenv('DASHSCOPE_DEFAULT_MODEL', 'qwen3.5-plus')

    # OpenRouter 配置
    # OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    # OPENROUTER_DEFAULT_MODEL = os.getenv('OPENROUTER_DEFAULT_MODEL', 'openai/gpt-3.5-turbo')

    # AI 服务配置
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', 2000))
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', 0.7))
    AI_REQUEST_TIMEOUT = int(os.getenv('AI_REQUEST_TIMEOUT', 30))

    # 会话配置
    SESSION_TIMEOUT = timedelta(hours=2)

    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

    # CORS 配置
    cors_origins_str = os.getenv('CORS_ORIGINS', '*')
    CORS_ORIGINS = ['*'] if cors_origins_str == '' else cors_origins_str.split(',')

    # 速率限制
    RATELIMIT_DEFAULT = "100 per minute"

    # 阿里云通义千问模型配置
    DASHSCOPE_MODELS = {
        'qwen3.5-plus': {
            'name': '通义千问 3.5 Plus',
            'description': '阿里云最新一代大语言模型',
            'max_tokens': 16384,
            'context_length': 256000
        },
        'qwen-plus': {
            'name': '通义千问 Plus',
            'description': '性能均衡的通用模型',
            'max_tokens': 8192,
            'context_length': 32768
        },
        'qwen-turbo': {
            'name': '通义千问 Turbo',
            'description': '快速响应模型',
            'max_tokens': 8192,
            'context_length': 32768
        }
    }

    # MySQL 配置
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

    # Mongodb 配置
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
