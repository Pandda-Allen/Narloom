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

def register_blueprints(app):
    from api.routes.login import login_bp
    from api.routes.user_profile import user_profile_bp

    # 使用配置文件中的API前缀
    api_prefix = app.config['API_PREFIX']

    app.register_blueprint(login_bp, url_prefix=f'{api_prefix}/login')
    app.register_blueprint(user_profile_bp, url_prefix=f'{api_prefix}/user_profile')



# app = create_app()

# if __name__ == '__main__':
#     port = int(os.getenv('PORT', 5000))
#     app.run(
#         host='0.0.0.0',
#         port=port,
#         debug=app.config['DEBUG']
#     )