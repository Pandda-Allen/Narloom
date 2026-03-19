import os
from flask import Flask, jsonify

def create_app(config_name='default'):
    app = Flask(__name__)

    # 加载配置
    from config import Config
    app.config.from_object(Config)
    Config.init_app(app)

    # 初始化数据库客户端
    init_mysql(app)
    init_mongo(app)

    # 初始化 AI 服务
    init_ai_service(app)

    # 初始化 Anime Tool 服务
    init_anime_tool_service(app)

    # 注册 Flask Blueprints
    register_blueprints(app)

    return app


def init_mysql(app):
    """初始化 MySQL 客户端"""
    from services.mysql_service import mysql_service

    mysql_service.init_app(app)

    # 触发初始化
    if mysql_service._initialized:
        app.logger.info("MySQL service is ready to use.")
    else:
        app.logger.error("Failed to initialize MySQL service.")

def init_mongo(app):
    """初始化 MongoDB 客户端"""
    from services.mongo_service import mongo_service

    mongo_service.init_app(app)

    # 触发初始化
    if mongo_service._initialized:
        app.logger.info("MongoDB service is ready to use.")
    else:
        app.logger.error("Failed to initialize MongoDB service.")

def init_ai_service(app):
    """初始化 AI Service"""
    from services.ai_service import qwen_ai_service

    qwen_ai_service.init_app(app)

    # 触发初始化
    if qwen_ai_service._initialized:
        app.logger.info("Qwen AI Service is ready to use.")
    else:
        app.logger.error("Failed to initialize Qwen AI Service.")

def init_anime_tool_service(app):
    """初始化 Anime Tool Service"""
    from services.anime_tool_service import anime_tool_service

    anime_tool_service.init_app(app)

    # 触发初始化
    if anime_tool_service._initialized:
        app.logger.info("Aliyun OSS service is ready to use.")
    else:
        app.logger.error("Failed to initialize Aliyun OSS service.")


def register_blueprints(app):
    from api.routes.user import user_bp
    from api.routes.work import work_bp
    from api.routes.chapter import chapter_bp
    from api.routes.asset import asset_bp
    from api.routes.ai import ai_bp
    from api.routes.anime_tool import anime_tool_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(asset_bp, url_prefix='/rest/v1/asset')
    app.register_blueprint(work_bp, url_prefix='/rest/v1/work')
    app.register_blueprint(chapter_bp, url_prefix='/rest/v1/chapter')
    app.register_blueprint(ai_bp, url_prefix='/rest/v1/ai')
    app.register_blueprint(anime_tool_bp, url_prefix='/rest/v1/anime-tool')
