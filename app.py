import os
from flask import Flask, jsonify

def create_app(config_name='default'):
    app = Flask(__name__)

    # 加载配置
    from config import Config
    app.config.from_object(Config)
    Config.init_app(app)

    # 初始化 Supabase 客户端
    init_supabase(app)

    # 初始化数据库客户端
    init_mysql(app)
    init_mongo(app)

    # 初始化 AI 服务
    init_ai_service(app)

    # 注册 Flask Blueprints
    register_blueprints(app)

    return app


def init_supabase(app):
    """初始化 Supabase 客户端"""
    from services.supabase_service import supabase_service

    supabase_service.init_app(app)

    # 触发初始化
    if supabase_service.client:
        app.logger.info("Supabase client is ready to use.")
    else:
        app.logger.error("Failed to initialize Supabase client.")

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
    from services.ai_service import deepseek_ai_service

    deepseek_ai_service.init_app(app)

    # 触发初始化
    if deepseek_ai_service._initialized:
        app.logger.info("DeepSeek AI Service is ready to use.")
    else:
        app.logger.error("Failed to initialize DeepSeek AI Service.")


def register_blueprints(app):
    from api.routes.user import login_bp, user_profile_bp, register_bp
    from api.routes.work import work_bp
    from api.routes.chapter import chapter_bp
    from api.routes.asset import asset_bp
    from api.routes.ai import ai_bp

    # 使用配置文件中的 API 前缀
    api_prefix = app.config['API_PREFIX']

    app.register_blueprint(login_bp, url_prefix='/login')
    app.register_blueprint(user_profile_bp, url_prefix='/user_profile')
    app.register_blueprint(register_bp, url_prefix='/register')
    app.register_blueprint(asset_bp, url_prefix='/rest/v1/asset')
    app.register_blueprint(work_bp, url_prefix='/rest/v1/work')
    app.register_blueprint(chapter_bp, url_prefix='/rest/v1/chapter')
    app.register_blueprint(ai_bp, url_prefix='/rest/v1/ai')
