import os
import logging
from logging.handlers import TimedRotatingFileHandler
from flask import Flask, jsonify

def create_app(config_name='default'):
    app = Flask(__name__)

    # 加载配置
    from config import Config
    app.config.from_object(Config)
    Config.init_app(app)

    # 配置日志处理器
    _setup_logging(app)

    # 初始化数据库客户端
    init_mysql(app)
    init_mongo(app)

    # 初始化 AI 服务
    init_ai_service(app)

    # 初始化对话历史服务
    init_conversation_history(app)

    # 初始化 OSS 服务（统一对象存储接口，包含 Picture 和 Video 服务）
    init_oss_service(app)

    # 初始化 Anime 服务（动画生成）
    init_anime_service(app)

    # 初始化视频生成服务
    init_video_generation_service(app)

    # 注册 Flask Blueprints
    register_blueprints(app)

    return app


def _setup_logging(app):
    """配置日志处理器，将日志写入 logs/narloom.log"""
    # 确保 logs 目录存在
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # 配置文件处理器
    log_file = os.path.join(logs_dir, 'narloom.log')
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='D',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # 添加到应用日志
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)


def init_mysql(app):
    """初始化 MySQL 客户端"""
    from services import mysql_service

    mysql_service.init_app(app)

    # 触发初始化
    if not mysql_service._initialized:
        app.logger.error("Failed to initialize MySQL service.")

def init_mongo(app):
    """初始化 MongoDB 客户端"""
    from services import mongo_service

    mongo_service.init_app(app)

    # 触发初始化
    if not mongo_service._initialized:
        app.logger.error("Failed to initialize MongoDB service.")

def init_ai_service(app):
    """初始化 AI Service"""
    from services.ai_service import qwen_ai_service

    qwen_ai_service.init_app(app)

    # 触发初始化
    if not qwen_ai_service._initialized:
        app.logger.error("Failed to initialize Qwen AI Service.")

def init_conversation_history(app):
    """初始化对话历史服务"""
    from services.conversation_history import conversation_history

    conversation_history.init_app(app)
    app.logger.info("Conversation history service initialized.")

def init_anime_service(app):
    """初始化 Anime Service（动画生成）"""
    from services.anime_service import anime_service
    # AnimeService 不需要特殊初始化，这里预留扩展位置

def init_video_generation_service(app):
    """初始化视频生成服务"""
    from services.video_generation_service import video_generation_service

    video_generation_service.init_app(app)

    # 触发初始化
    if not video_generation_service._initialized:
        app.logger.error("Failed to initialize video generation service.")

def init_oss_service(app):
    """初始化 OSS Service（统一对象存储接口，包含 Picture 和 Video 服务）"""
    from services.storage import oss_service

    oss_service.init_app(app)

    # 触发初始化
    if not oss_service._initialized:
        app.logger.error("Failed to initialize OSS service.")

def register_blueprints(app):
    from api.routes.user import user_bp
    from api.routes.work import work_bp
    from api.routes.chapter import chapter_bp
    from api.routes.asset import asset_bp
    from api.routes.ai import ai_bp
    from api.routes.pictures import picture_bp
    from api.routes.anime import anime_bp
    from api.routes.shots import shots_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(asset_bp, url_prefix='/rest/v1/asset')
    app.register_blueprint(work_bp, url_prefix='/rest/v1/work')
    app.register_blueprint(chapter_bp, url_prefix='/rest/v1/chapter')
    app.register_blueprint(ai_bp, url_prefix='/rest/v1/ai')
    app.register_blueprint(picture_bp, url_prefix='/rest/v1/picture')
    app.register_blueprint(anime_bp, url_prefix='/rest/v1/anime')
    app.register_blueprint(shots_bp, url_prefix='/rest/v1/shots')
