import os
from flask import Flask, jsonify

def create_app(config_name='default'): 
    app = Flask(__name__)

    # 加载配置
    from config import Config
    app.config.from_object(Config)
    Config.init_app(app)

    # 初始化Supabase客户端
    init_supabase(app)

    # 注册Flask Blueprints
    register_blueprints(app)

    return app


def init_supabase(app):
    """初始化Supabase客户端"""
    from services.supabase_service import supabase_service

    supabase_service.init_app(app)

    # 触发初始化
    if supabase_service.client:
        app.logger.info("Supabase client is ready to use.")
    else:
        app.logger.error("Failed to initialize Supabase client.")

def init_ai_service(app):
    """初始化AIService"""
    from services.ai_service import deepseek_ai_service

    deepseek_ai_service.init_app(app)

    # 触发初始化
    if deepseek_ai_service._initialized:
        app.logger.info("DeepSeek AI Service is ready to use.")
    else:
        app.logger.error("Failed to initialize DeepSeek AI Service.")


def register_blueprints(app):
    from api.routes.login import login_bp
    from api.routes.user_profile import user_profile_bp
    from api.routes.asset import asset_bp
    from api.routes.work import work_bp
    from api.routes.ai import ai_bp
    from api.routes.work_asset_map import work_asset_map_bp

    # 使用配置文件中的API前缀
    api_prefix = app.config['API_PREFIX']

    app.register_blueprint(login_bp, url_prefix='/login')
    app.register_blueprint(user_profile_bp, url_prefix='/user_profile')
    app.register_blueprint(asset_bp, url_prefix='/rest/v1/asset')
    app.register_blueprint(work_bp, url_prefix='/rest/v1/work')
    app.register_blueprint(ai_bp, url_prefix='/rest/v1/ai')
    app.register_blueprint(work_asset_map_bp, url_prefix='/rest/v1/work_asset_map')
