"""
测试工具函数。
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.general_helper import validate_required_fields

def test_validate_required_fields():
    """测试必需字段验证"""
    data = {'name': 'John', 'age': 30}
    # 字段存在，应该通过
    validate_required_fields(data, ['name'])
    # 字段缺失，应该抛出ValueError
    try:
        validate_required_fields(data, ['email'])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'email' in str(e)
    print("validate_required_fields test passed")

if __name__ == '__main__':
    test_validate_required_fields()
    print("All helper tests completed.")