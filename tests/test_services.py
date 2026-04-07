"""
测试服务类的基本功能。
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import MySQLService, MongoService

def test_singleton_pattern():
    """测试单例模式"""
    instance1 = MySQLService()
    instance2 = MySQLService()
    assert instance1 is instance2, "MySQLService should be a singleton"

    instance3 = MongoService()
    instance4 = MongoService()
    assert instance3 is instance4, "MongoService should be a singleton"
    print("OK Singleton pattern test passed")

def test_service_initialization():
    """测试服务初始化（不实际连接数据库）"""
    # 这些测试不会真正初始化，因为需要Flask app上下文
    # 但我们可以检查类结构
    mysql = MySQLService()
    assert hasattr(mysql, 'init_app')
    assert hasattr(mysql, '_ensure_connection')

    mongo = MongoService()
    assert hasattr(mongo, 'init_app')
    assert hasattr(mongo, '_ensure_collection')
    print("OK Service initialization test passed")

if __name__ == '__main__':
    test_singleton_pattern()
    test_service_initialization()
    print("All service tests completed.")