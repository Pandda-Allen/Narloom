"""
测试Flask应用。
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

def test_app_factory():
    """测试应用工厂"""
    app = create_app()
    assert app is not None
    assert app.name == 'app'
    # 检查蓝图是否注册
    blueprints = list(app.blueprints.keys())
    expected_blueprints = ['login', 'user_profile', 'asset', 'work', 'chapter', 'ai', 'work_asset_map']
    for bp in expected_blueprints:
        assert bp in blueprints, f"Blueprint {bp} not registered"
    print("OK App factory test passed")

def test_config_loading():
    """测试配置加载"""
    app = create_app()
    # 检查关键配置
    assert 'SECRET_KEY' in app.config
    assert 'DEBUG' in app.config
    assert 'API_PREFIX' in app.config
    print("OK Config loading test passed")

if __name__ == '__main__':
    test_app_factory()
    test_config_loading()
    print("All app tests completed.")