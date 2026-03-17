"""
测试配置加载。
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config

def test_config_defaults():
    """测试配置默认值"""
    # 测试默认值
    assert Config.SECRET_KEY is not None
    assert isinstance(Config.DEBUG, bool)
    assert Config.API_PREFIX is not None
    print("Config defaults test passed")

def test_mysql_config():
    """测试MySQL配置"""
    # 确保表名配置不是同一个环境变量
    # 注意：目前配置有错误，MYSQL_TABLE_ASSETS等都是从MYSQL_TABLE读取
    # 这个测试会失败，提醒修复
    assert Config.MYSQL_TABLE_ASSETS != Config.MYSQL_TABLE_WORKS, "Table names should be different"
    print("MySQL config test passed")

if __name__ == '__main__':
    test_config_defaults()
    try:
        test_mysql_config()
    except AssertionError as e:
        print(f"MySQL config test failed: {e}")
        print("  This is expected due to configuration error in config.py")
    print("All tests completed.")