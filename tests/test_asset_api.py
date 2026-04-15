"""
测试资产模块 API 接口。
覆盖所有 asset 相关接口的数据库读写操作。
"""
import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
import json

# 测试用用户 ID
TEST_USER_ID = str(uuid.uuid4())


def create_test_asset_data(asset_type='character', work_id=None):
    """生成测试资产数据"""
    return {
        'type': asset_type,
        'user_id': TEST_USER_ID,
        'work_id': work_id,
        'asset_data': {
            'name': f'Test {asset_type}',
            'description': f'Test {asset_type} description',
            'image_url': 'https://example.com/test.jpg'
        }
    }


def test_create_asset():
    """测试创建资产接口"""
    app = create_app()

    with app.test_client() as client:
        # 测试创建 character 类型资产
        asset_data = create_test_asset_data('character')
        response = client.post(
            '/rest/v1/asset/createNewAsset',
            data=json.dumps(asset_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Create asset failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert 'asset_id' in result['data'], f"Response should contain asset_id: {result}"
        assert result['data']['asset_type'] == 'character', f"Asset type mismatch: {result}"
        assert result['data']['user_id'] == TEST_USER_ID, f"User ID mismatch: {result}"

        asset_id = result['data']['asset_id']
        print(f"  Created asset: {asset_id}")
        return asset_id


def test_create_world_asset():
    """测试创建 world 类型资产"""
    app = create_app()

    with app.test_client() as client:
        asset_data = create_test_asset_data('world')
        response = client.post(
            '/rest/v1/asset/createNewAsset',
            data=json.dumps(asset_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Create world asset failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success'
        assert result['data']['asset_type'] == 'world'

        print(f"  Created world asset: {result['data']['asset_id']}")
        return result['data']['asset_id']


def test_get_asset_by_id():
    """测试获取资产详情接口"""
    app = create_app()

    # 先创建一个资产
    with app.test_client() as client:
        asset_data = create_test_asset_data('character')
        create_response = client.post(
            '/rest/v1/asset/createNewAsset',
            data=json.dumps(asset_data),
            content_type='application/json'
        )
        asset_id = json.loads(create_response.data)['data']['asset_id']

    # 测试获取资产
    with app.test_client() as client:
        response = client.get(f'/rest/v1/asset/getAssetById?asset_id={asset_id}')

        assert response.status_code == 200, f"Get asset failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert result['data']['asset_id'] == asset_id, f"Asset ID mismatch: {result}"
        assert 'asset_data' in result['data'], f"Response should contain asset_data: {result}"
        assert result['data']['asset_data']['name'] == 'Test character', f"Asset data name mismatch: {result}"

        print(f"  Retrieved asset: {asset_id}")
        return asset_id


def test_update_asset():
    """测试更新资产接口"""
    app = create_app()

    # 先创建一个资产
    with app.test_client() as client:
        asset_data = create_test_asset_data('character')
        create_response = client.post(
            '/rest/v1/asset/createNewAsset',
            data=json.dumps(asset_data),
            content_type='application/json'
        )
        asset_id = json.loads(create_response.data)['data']['asset_id']

    # 测试更新资产
    with app.test_client() as client:
        update_data = {
            'asset_id': asset_id,
            'asset_data': {
                'name': 'Updated Character Name',
                'description': 'Updated description',
                'image_url': 'https://example.com/updated.jpg'
            }
        }
        response = client.post(
            '/rest/v1/asset/updateAssetById',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Update asset failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert result['data']['asset_data']['name'] == 'Updated Character Name', f"Name not updated: {result}"
        assert result['data']['asset_data']['description'] == 'Updated description', f"Description not updated: {result}"

        # 验证更新后的数据
        get_response = client.get(f'/rest/v1/asset/getAssetById?asset_id={asset_id}')
        get_result = json.loads(get_response.data)
        assert get_result['data']['asset_data']['name'] == 'Updated Character Name'

        print(f"  Updated asset: {asset_id}")
        return asset_id


def test_get_assets_by_user_id():
    """测试获取用户资产列表接口"""
    app = create_app()

    # 先创建几个资产
    with app.test_client() as client:
        for i in range(5):
            asset_data = {
                'type': 'character' if i % 2 == 0 else 'world',
                'user_id': TEST_USER_ID,
                'asset_data': {
                    'name': f'Test Asset {i+1}',
                    'description': f'Test description {i+1}'
                }
            }
            client.post(
                '/rest/v1/asset/createNewAsset',
                data=json.dumps(asset_data),
                content_type='application/json'
            )

    # 测试获取用户资产列表
    with app.test_client() as client:
        response = client.get(f'/rest/v1/asset/getAssetsByUserId?user_id={TEST_USER_ID}')

        assert response.status_code == 200, f"Get assets list failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert len(result['data']) >= 5, f"Should have at least 5 assets: {result}"

        print(f"  Retrieved {len(result['data'])} assets for user")


def test_get_assets_by_type():
    """测试按类型筛选资产接口"""
    app = create_app()

    # 先创建特定类型的资产
    with app.test_client() as client:
        for i in range(3):
            asset_data = {
                'type': 'character',
                'user_id': TEST_USER_ID,
                'asset_data': {
                    'name': f'Test Character {i+1}',
                    'description': f'Test description {i+1}'
                }
            }
            client.post(
                '/rest/v1/asset/createNewAsset',
                data=json.dumps(asset_data),
                content_type='application/json'
            )

    # 测试按类型筛选
    with app.test_client() as client:
        response = client.get(f'/rest/v1/asset/getAssetsByUserId?user_id={TEST_USER_ID}&type=character')

        assert response.status_code == 200, f"Get assets by type failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert len(result['data']) >= 3, f"Should have at least 3 character assets: {result}"

        # 验证所有返回的资产都是 character 类型
        for asset in result['data']:
            assert asset['asset_type'] == 'character', f"Asset type should be character: {asset}"

        print(f"  Retrieved {len(result['data'])} character assets")


def test_get_assets_by_work_id():
    """测试按作品 ID 筛选资产接口"""
    app = create_app()

    # 先创建一个作品
    with app.test_client() as client:
        work_data = {
            'author_id': TEST_USER_ID,
            'title': 'Test Work for Assets',
            'work_type': 'novel'
        }
        create_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(create_response.data)['data']['work_id']

        # 创建关联到作品的资产
        for i in range(3):
            asset_data = {
                'type': 'character',
                'user_id': TEST_USER_ID,
                'work_id': work_id,
                'asset_data': {
                    'name': f'Test Work Asset {i+1}',
                    'description': f'Test description {i+1}'
                }
            }
            client.post(
                '/rest/v1/asset/createNewAsset',
                data=json.dumps(asset_data),
                content_type='application/json'
            )

    # 测试按作品 ID 筛选
    with app.test_client() as client:
        response = client.get(f'/rest/v1/asset/getAssetsByUserId?user_id={TEST_USER_ID}&work_id={work_id}')

        assert response.status_code == 200, f"Get assets by work failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert len(result['data']) >= 3, f"Should have at least 3 work assets: {result}"

        print(f"  Retrieved {len(result['data'])} assets for work")


def test_delete_asset():
    """测试删除资产接口"""
    app = create_app()

    # 先创建一个资产
    with app.test_client() as client:
        asset_data = create_test_asset_data('character')
        create_response = client.post(
            '/rest/v1/asset/createNewAsset',
            data=json.dumps(asset_data),
            content_type='application/json'
        )
        asset_id = json.loads(create_response.data)['data']['asset_id']

    # 测试删除资产
    with app.test_client() as client:
        response = client.post(
            '/rest/v1/asset/deleteAssetById',
            data=json.dumps({'asset_id': asset_id}),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Delete asset failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"

        # 验证资产已被删除
        get_response = client.get(f'/rest/v1/asset/getAssetById?asset_id={asset_id}')
        assert get_response.status_code == 404, f"Asset should be deleted: {get_response.data}"

        print(f"  Deleted asset: {asset_id}")


def test_asset_cascade_delete():
    """测试资产级联删除（MySQL + MongoDB）"""
    app = create_app()

    # 创建一个带有 MongoDB 详细数据的资产
    with app.test_client() as client:
        asset_data = {
            'type': 'character',
            'user_id': TEST_USER_ID,
            'asset_data': {
                'name': 'Cascade Test Character',
                'description': 'Test description for cascade delete',
                'extra_field': 'extra_data'
            }
        }
        create_response = client.post(
            '/rest/v1/asset/createNewAsset',
            data=json.dumps(asset_data),
            content_type='application/json'
        )
        asset_id = json.loads(create_response.data)['data']['asset_id']

    # 验证资产存在
    with app.test_client() as client:
        get_response = client.get(f'/rest/v1/asset/getAssetById?asset_id={asset_id}')
        assert get_response.status_code == 200

    # 删除资产
    with app.test_client() as client:
        response = client.post(
            '/rest/v1/asset/deleteAssetById',
            data=json.dumps({'asset_id': asset_id}),
            content_type='application/json'
        )
        assert response.status_code == 200

    # 验证资产已被彻底删除
    with app.test_client() as client:
        get_response = client.get(f'/rest/v1/asset/getAssetById?asset_id={asset_id}')
        assert get_response.status_code == 404, "Asset should be completely deleted"

        print(f"  Verified cascade delete for asset: {asset_id}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Starting Asset API Tests")
    print("=" * 50)

    tests = [
        ("Create Character Asset", test_create_asset),
        ("Create World Asset", test_create_world_asset),
        ("Get Asset By ID", test_get_asset_by_id),
        ("Update Asset", test_update_asset),
        ("Get Assets By User ID", test_get_assets_by_user_id),
        ("Get Assets By Type", test_get_assets_by_type),
        ("Get Assets By Work ID", test_get_assets_by_work_id),
        ("Delete Asset", test_delete_asset),
        ("Asset Cascade Delete", test_asset_cascade_delete),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n[{test_name}]")
            test_func()
            passed += 1
            print("  PASSED")
        except AssertionError as e:
            print(f"  FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
