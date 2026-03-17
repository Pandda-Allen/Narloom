"""
统一测试运行器
运行此文件将执行所有测试用例
"""
import sys
import os
import traceback
from datetime import datetime

# 设置 UTF-8 编码（Windows 兼容性）
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 测试结果统计
test_results = {
    'passed': 0,
    'failed': 0,
    'errors': []
}


def print_header(text):
    """打印测试模块标题"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)


def print_result(name, passed, error=None):
    """打印测试结果"""
    status = "PASS" if passed else "FAIL"
    marker = "[OK]" if passed else "[ERR]"
    print(f"  {marker} {name}")
    if passed:
        test_results['passed'] += 1
    else:
        test_results['failed'] += 1
        if error:
            test_results['errors'].append((name, str(error)))


# ==================== 测试：App 工厂 ====================
def run_app_tests():
    """运行应用测试"""
    print_header("App 测试")

    from tests.test_app import test_app_factory, test_config_loading

    try:
        test_app_factory()
        print_result("test_app_factory", True)
    except Exception as e:
        print_result("test_app_factory", False, e)

    try:
        test_config_loading()
        print_result("test_config_loading", True)
    except Exception as e:
        print_result("test_config_loading", False, e)


# ==================== 测试：配置 ====================
def run_config_tests():
    """运行配置测试"""
    print_header("配置测试")

    from tests.test_config import test_config_defaults, test_mysql_config

    try:
        test_config_defaults()
        print_result("test_config_defaults", True)
    except Exception as e:
        print_result("test_config_defaults", False, e)

    try:
        test_mysql_config()
        print_result("test_mysql_config", True)
    except AssertionError as e:
        print_result("test_mysql_config", False, e)
        print("      (预期内的失败：config.py 中表名配置有误)")
    except Exception as e:
        print_result("test_mysql_config", False, e)


# ==================== 测试：工具函数 ====================
def run_helper_tests():
    """运行工具函数测试"""
    print_header("工具函数测试")

    from tests.test_helpers import test_validate_required_fields

    try:
        test_validate_required_fields()
        print_result("test_validate_required_fields", True)
    except Exception as e:
        print_result("test_validate_required_fields", False, e)


# ==================== 测试：服务类 ====================
def run_service_tests():
    """运行服务类测试"""
    print_header("服务类测试")

    from tests.test_services import test_singleton_pattern, test_service_initialization

    try:
        test_singleton_pattern()
        print_result("test_singleton_pattern", True)
    except Exception as e:
        print_result("test_singleton_pattern", False, e)

    try:
        test_service_initialization()
        print_result("test_service_initialization", True)
    except Exception as e:
        print_result("test_service_initialization", False, e)


# ==================== 测试：数据库集成 ====================
def run_database_tests():
    """运行数据库集成测试"""
    print_header("数据库集成测试 (需要数据库连接)")

    from tests.test_database_integration import (
        setup_module,
        test_mysql_asset_crud,
        test_mongo_asset_data_crud,
        test_mysql_work_crud,
        test_mysql_chapter_crud,
        test_mongo_work_details,
        test_cross_database_interaction
    )

    # 初始化
    try:
        setup_module()
        print("  [INFO] 数据库服务初始化完成")
    except Exception as e:
        print(f"  [WARN] 数据库服务初始化失败：{e}")
        print("  [INFO] 跳过数据库集成测试")
        return

    # 运行测试
    db_tests = [
        ("test_mysql_asset_crud", test_mysql_asset_crud),
        ("test_mongo_asset_data_crud", test_mongo_asset_data_crud),
        ("test_mysql_work_crud", test_mysql_work_crud),
        ("test_mysql_chapter_crud", test_mysql_chapter_crud),
        ("test_mongo_work_details", test_mongo_work_details),
        ("test_cross_database_interaction", test_cross_database_interaction),
    ]

    for name, test_func in db_tests:
        try:
            test_func()
            print_result(name, True)
        except Exception as e:
            print_result(name, False, e)


# ==================== 主函数 ====================
def main():
    """运行所有测试"""
    start_time = datetime.now()

    print("\n" + "#" * 60)
    print("#  测试套件 - All Tests Suite")
    print("#  开始时间：" + start_time.strftime("%Y-%m-%d %H:%M:%S"))
    print("#" * 60)

    # 运行所有测试模块
    run_app_tests()
    run_config_tests()
    run_helper_tests()
    run_service_tests()
    run_database_tests()

    # 打印汇总
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print_header("测试汇总")
    print(f"  总测试数：{test_results['passed'] + test_results['failed']}")
    print(f"  通过：{test_results['passed']}")
    print(f"  失败：{test_results['failed']}")
    print(f"  运行时间：{duration:.2f}秒")

    if test_results['errors']:
        print("\n  失败详情:")
        for name, error in test_results['errors']:
            print(f"    - {name}: {error}")

    print("\n" + "=" * 60)
    if test_results['failed'] == 0:
        print("  [OK] 所有测试通过!")
        return 0
    else:
        print(f"  [ERR] {test_results['failed']} 个测试失败")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
