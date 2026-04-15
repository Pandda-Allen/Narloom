"""
测试作品模块 API 接口。
覆盖所有 work 相关接口的数据库读写操作。
"""
import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
import json

# 测试用作者 ID
TEST_AUTHOR_ID = str(uuid.uuid4())


def create_test_work_data(title=None, work_type='novel'):
    """生成测试作品数据"""
    return {
        'author_id': TEST_AUTHOR_ID,
        'title': title or f'Test Work {uuid.uuid4()[:8]}',
        'genre': '测试类型',
        'tags': ['标签 1', '标签 2'],
        'status': '连载中',
        'description': '测试作品描述',
        'work_type': work_type
    }


def test_create_work():
    """测试创建作品接口"""
    app = create_app()

    with app.test_client() as client:
        work_data = create_test_work_data('Test Novel', 'novel')
        response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Create work failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert 'work_id' in result['data'], f"Response should contain work_id: {result}"
        assert result['data']['title'] == 'Test Novel', f"Title mismatch: {result}"
        assert result['data']['work_type'] == 'novel', f"Work type mismatch: {result}"

        work_id = result['data']['work_id']
        print(f"  Created work: {work_id}")
        return work_id


def test_get_work_by_id():
    """测试获取作品详情接口"""
    app = create_app()

    with app.test_client() as client:
        work_data = create_test_work_data('Test Get Work')
        create_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(create_response.data)['data']['work_id']

    with app.test_client() as client:
        response = client.get(f'/rest/v1/work/getWorkById?work_id={work_id}')

        assert response.status_code == 200, f"Get work failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert result['data']['work_id'] == work_id, f"Work ID mismatch: {result}"
        assert result['data']['title'] == 'Test Get Work', f"Title mismatch: {result}"
        assert 'asset_ids' in result['data'], f"Response should contain asset_ids: {result}"
        assert 'novel_ids' in result['data'], f"Response should contain novel_ids: {result}"
        assert 'anime_ids' in result['data'], f"Response should contain anime_ids: {result}"

        print(f"  Retrieved work: {work_id}")
        return work_id


def test_update_work():
    """测试更新作品接口"""
    app = create_app()

    with app.test_client() as client:
        work_data = create_test_work_data('Test Update Work Original')
        create_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(create_response.data)['data']['work_id']

    with app.test_client() as client:
        update_data = {
            'work_id': work_id,
            'title': 'Test Update Work Modified',
            'status': '已完结',
            'description': '更新后的描述'
        }
        response = client.post(
            '/rest/v1/work/updateWorkById',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Update work failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert result['data']['title'] == 'Test Update Work Modified', f"Title not updated: {result}"
        assert result['data']['status'] == '已完结', f"Status not updated: {result}"

        get_response = client.get(f'/rest/v1/work/getWorkById?work_id={work_id}')
        get_result = json.loads(get_response.data)
        assert get_result['data']['title'] == 'Test Update Work Modified'
        assert get_result['data']['status'] == '已完结'

        print(f"  Updated work: {work_id}")
        return work_id


def test_get_works_by_author_id():
    """测试获取作者作品列表接口"""
    app = create_app()

    with app.test_client() as client:
        for i in range(3):
            work_data = create_test_work_data(f'Test List Work {i+1}')
            client.post(
                '/rest/v1/work/createWork',
                data=json.dumps(work_data),
                content_type='application/json'
            )

    with app.test_client() as client:
        response = client.get(f'/rest/v1/work/getWorksByAuthorId?author_id={TEST_AUTHOR_ID}')

        assert response.status_code == 200, f"Get works list failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert len(result['data']) >= 3, f"Should have at least 3 works: {result}"

        print(f"  Retrieved {len(result['data'])} works for author")


def test_add_asset_to_work():
    """测试添加资产到作品接口"""
    app = create_app()

    with app.test_client() as client:
        work_data = create_test_work_data('Test Add Asset Work')
        create_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(create_response.data)['data']['work_id']

        asset_data = {
            'type': 'character',
            'user_id': TEST_AUTHOR_ID,
            'work_id': work_id,
            'asset_data': {
                'name': 'Test Character',
                'description': 'Test character description'
            }
        }
        asset_response = client.post(
            '/rest/v1/asset/createNewAsset',
            data=json.dumps(asset_data),
            content_type='application/json'
        )
        result = json.loads(asset_response.data)
        assert result['status'] == 'success', f"Create asset failed: {result}"
        asset_id = result['data']['asset_id']

    with app.test_client() as client:
        add_data = {
            'work_id': work_id,
            'asset_id': asset_id
        }
        response = client.post(
            '/rest/v1/work/addAssetToWork',
            data=json.dumps(add_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Add asset to work failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert 'asset_ids' in result['data'], f"Response should contain asset_ids: {result}"
        assert asset_id in result['data']['asset_ids'], f"Asset should be in work: {result}"

        print(f"  Added asset {asset_id} to work {work_id}")
        return work_id, asset_id


def test_get_assets_by_work_id():
    """测试获取作品关联资产接口"""
    app = create_app()

    with app.test_client() as client:
        work_data = create_test_work_data('Test Get Assets Work')
        create_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(create_response.data)['data']['work_id']

        asset_ids = []
        for i in range(2):
            asset_data = {
                'type': 'character' if i == 0 else 'world',
                'user_id': TEST_AUTHOR_ID,
                'work_id': work_id,
                'asset_data': {
                    'name': f'Test Asset {i+1}',
                    'description': f'Test description {i+1}'
                }
            }
            asset_response = client.post(
                '/rest/v1/asset/createNewAsset',
                data=json.dumps(asset_data),
                content_type='application/json'
            )
            result = json.loads(asset_response.data)
            assert result['status'] == 'success', f"Create asset failed: {result}"
            asset_ids.append(result['data']['asset_id'])

        for asset_id in asset_ids:
            client.post(
                '/rest/v1/work/addAssetToWork',
                data=json.dumps({'work_id': work_id, 'asset_id': asset_id}),
                content_type='application/json'
            )

    with app.test_client() as client:
        response = client.get(f'/rest/v1/work/getAssetsByWorkId?work_id={work_id}')

        assert response.status_code == 200, f"Get assets by work failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert 'character' in result['data'], f"Response should contain character key: {result}"
        assert 'world' in result['data'], f"Response should contain world key: {result}"

        print(f"  Retrieved assets for work {work_id}")


def test_remove_asset_from_work():
    """测试从作品移除资产接口"""
    app = create_app()

    with app.test_client() as client:
        work_data = create_test_work_data('Test Remove Asset Work')
        create_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(create_response.data)['data']['work_id']

        asset_data = {
            'type': 'character',
            'user_id': TEST_AUTHOR_ID,
            'work_id': work_id,
            'asset_data': {
                'name': 'Test Remove Character',
                'description': 'Test remove description'
            }
        }
        asset_response = client.post(
            '/rest/v1/asset/createNewAsset',
            data=json.dumps(asset_data),
            content_type='application/json'
        )
        result = json.loads(asset_response.data)
        assert result['status'] == 'success', f"Create asset failed: {result}"
        asset_id = result['data']['asset_id']

        client.post(
            '/rest/v1/work/addAssetToWork',
            data=json.dumps({'work_id': work_id, 'asset_id': asset_id}),
            content_type='application/json'
        )

    with app.test_client() as client:
        remove_data = {
            'work_id': work_id,
            'asset_id': asset_id
        }
        response = client.post(
            '/rest/v1/work/removeAssetFromWork',
            data=json.dumps(remove_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Remove asset from work failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"

        get_response = client.get(f'/rest/v1/work/getAssetsByWorkId?work_id={work_id}')
        get_result = json.loads(get_response.data)

        all_assets = get_result['data'].get('character', []) + get_result['data'].get('world', [])
        assert not any(a['asset_id'] == asset_id for a in all_assets), \
            f"Asset should be removed: {get_result}"

        print(f"  Removed asset {asset_id} from work {work_id}")


def test_delete_work():
    """测试删除作品接口"""
    app = create_app()

    with app.test_client() as client:
        work_data = create_test_work_data('Test Delete Work')
        create_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(create_response.data)['data']['work_id']

    with app.test_client() as client:
        response = client.post(
            '/rest/v1/work/deleteWorkById',
            data=json.dumps({'work_id': work_id}),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Delete work failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"

        get_response = client.get(f'/rest/v1/work/getWorkById?work_id={work_id}')
        assert get_response.status_code == 404, f"Work should be deleted: {get_response.data}"

        print(f"  Deleted work: {work_id}")


def test_create_anime_work():
    """测试创建动画作品"""
    app = create_app()

    with app.test_client() as client:
        work_data = create_test_work_data('Test Anime Work', 'anime')
        response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Create anime work failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success'
        assert result['data']['work_type'] == 'anime'

        print(f"  Created anime work: {result['data']['work_id']}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Starting Work API Tests")
    print("=" * 50)

    tests = [
        ("Create Work", test_create_work),
        ("Get Work By ID", test_get_work_by_id),
        ("Update Work", test_update_work),
        ("Get Works By Author ID", test_get_works_by_author_id),
        ("Add Asset To Work", test_add_asset_to_work),
        ("Get Assets By Work ID", test_get_assets_by_work_id),
        ("Remove Asset From Work", test_remove_asset_from_work),
        ("Delete Work", test_delete_work),
        ("Create Anime Work", test_create_anime_work),
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
