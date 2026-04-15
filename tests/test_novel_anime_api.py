"""
测试 Novel 和 Anime 模块 API 接口。
覆盖所有数据库读写操作。
"""
import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
import json

# 测试用用户 ID
TEST_USER_ID = str(uuid.uuid4())
TEST_AUTHOR_ID = TEST_USER_ID


# ==================== Novel 模块测试 ====================

def create_test_novel_data(work_id, novel_number=None):
    """生成测试小说章节数据"""
    return {
        'work_id': work_id,
        'author_id': TEST_AUTHOR_ID,
        'novel_number': novel_number or 1,
        'novel_title': 'Test Chapter Title',
        'content': 'This is test chapter content.',
        'status': 'published',
        'word_count': 1000,
        'description': 'Test chapter description'
    }


def test_create_novel():
    """测试创建小说章节接口"""
    app = create_app()

    # 先创建一个作品
    with app.test_client() as client:
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Novel',
            'work_type': 'novel'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

    # 测试创建 novel
    with app.test_client() as client:
        novel_data = create_test_novel_data(work_id)
        response = client.post(
            '/rest/v1/novel/createNovel',
            data=json.dumps(novel_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Create novel failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert 'novel_id' in result['data'], f"Response should contain novel_id: {result}"
        assert result['data']['novel_title'] == 'Test Chapter Title', f"Title mismatch: {result}"
        assert result['data']['work_id'] == work_id, f"Work ID mismatch: {result}"

        novel_id = result['data']['novel_id']
        print(f"  Created novel: {novel_id}")
        return novel_id, work_id


def test_get_novel_by_work_id():
    """测试根据作品 ID 获取小说章节列表"""
    app = create_app()

    # 先创建作品和章节
    with app.test_client() as client:
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Novels List',
            'work_type': 'novel'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        # 创建 3 个章节
        for i in range(3):
            novel_data = {
                'work_id': work_id,
                'author_id': TEST_AUTHOR_ID,
                'novel_number': i + 1,
                'novel_title': f'Chapter {i+1}',
                'content': f'Content for chapter {i+1}',
                'status': 'published'
            }
            client.post(
                '/rest/v1/novel/createNovel',
                data=json.dumps(novel_data),
                content_type='application/json'
            )

    # 测试获取章节列表
    with app.test_client() as client:
        response = client.get(f'/rest/v1/novel/getNovelByWorkId?work_id={work_id}')

        assert response.status_code == 200, f"Get novels failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert len(result['data']) == 3, f"Should have 3 novels: {result}"

        print(f"  Retrieved {len(result['data'])} novels for work")


def test_update_novel():
    """测试更新小说章节接口"""
    app = create_app()

    # 先创建作品和章节
    with app.test_client() as client:
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Update',
            'work_type': 'novel'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        novel_data = {
            'work_id': work_id,
            'author_id': TEST_AUTHOR_ID,
            'novel_number': 1,
            'novel_title': 'Original Title',
            'content': 'Original content',
            'status': 'draft'
        }
        create_response = client.post(
            '/rest/v1/novel/createNovel',
            data=json.dumps(novel_data),
            content_type='application/json'
        )
        novel_id = json.loads(create_response.data)['data']['novel_id']

    # 测试更新章节
    with app.test_client() as client:
        update_data = {
            'novel_id': novel_id,
            'novel_title': 'Updated Title',
            'content': 'Updated content here',
            'status': 'published'
        }
        response = client.post(
            '/rest/v1/novel/updateNovelById',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Update novel failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert result['data']['novel_title'] == 'Updated Title', f"Title not updated: {result}"
        assert result['data']['status'] == 'published', f"Status not updated: {result}"

        print(f"  Updated novel: {novel_id}")
        return novel_id


def test_delete_novel():
    """测试删除小说章节接口"""
    app = create_app()

    # 先创建作品和章节
    with app.test_client() as client:
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Delete',
            'work_type': 'novel'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        novel_data = {
            'work_id': work_id,
            'author_id': TEST_AUTHOR_ID,
            'novel_number': 1,
            'novel_title': 'To Be Deleted',
            'content': 'This chapter will be deleted',
            'status': 'draft'
        }
        create_response = client.post(
            '/rest/v1/novel/createNovel',
            data=json.dumps(novel_data),
            content_type='application/json'
        )
        novel_id = json.loads(create_response.data)['data']['novel_id']

    # 测试删除章节
    with app.test_client() as client:
        response = client.post(
            '/rest/v1/novel/deleteNovelById',
            data=json.dumps({'novel_id': novel_id}),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Delete novel failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"

        # 验证章节已被删除
        get_response = client.get(f'/rest/v1/novel/getNovelByWorkId?work_id={work_id}')
        get_result = json.loads(get_response.data)
        assert len(get_result['data']) == 0, f"Novel should be deleted: {get_result}"

        print(f"  Deleted novel: {novel_id}")


# ==================== Anime 模块测试 ====================

def create_test_anime_data(work_id, anime_number=None):
    """生成测试动画镜头数据"""
    return {
        'work_id': work_id,
        'author_id': TEST_AUTHOR_ID,
        'anime_number': anime_number or 1,
        'description': 'Test anime shot description',
        'notes': 'Test notes'
    }


def test_create_anime():
    """测试创建动画镜头接口"""
    app = create_app()

    # 先创建一个作品（动画类型）
    with app.test_client() as client:
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Anime',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

    # 测试创建 anime
    with app.test_client() as client:
        anime_data = create_test_anime_data(work_id)
        response = client.post(
            '/rest/v1/anime/createAnime',
            data=json.dumps(anime_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Create anime failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert 'anime_id' in result['data'], f"Response should contain anime_id: {result}"
        assert result['data']['anime_number'] == 1, f"Anime number mismatch: {result}"
        assert result['data']['work_id'] == work_id, f"Work ID mismatch: {result}"

        anime_id = result['data']['anime_id']
        print(f"  Created anime: {anime_id}")
        return anime_id, work_id


def test_get_animes_by_work_id():
    """测试根据作品 ID 获取动画镜头列表"""
    app = create_app()

    # 先创建作品和镜头
    with app.test_client() as client:
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Animes List',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        # 创建 3 个镜头
        for i in range(3):
            anime_data = {
                'work_id': work_id,
                'author_id': TEST_AUTHOR_ID,
                'anime_number': i + 1,
                'description': f'Shot {i+1} description',
                'notes': f'Shot {i+1} notes'
            }
            client.post(
                '/rest/v1/anime/createAnime',
                data=json.dumps(anime_data),
                content_type='application/json'
            )

    # 测试获取镜头列表
    with app.test_client() as client:
        response = client.get(f'/rest/v1/anime/getAnimesByWorkId?work_id={work_id}')

        assert response.status_code == 200, f"Get animes failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert len(result['data']) == 3, f"Should have 3 animes: {result}"

        print(f"  Retrieved {len(result['data'])} animes for work")


def test_confirm_anime():
    """测试确认动画镜头接口"""
    app = create_app()

    # 先创建作品和镜头
    with app.test_client() as client:
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Confirm',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        anime_data = create_test_anime_data(work_id)
        create_response = client.post(
            '/rest/v1/anime/createAnime',
            data=json.dumps(anime_data),
            content_type='application/json'
        )
        anime_id = json.loads(create_response.data)['data']['anime_id']

    # 测试确认镜头
    with app.test_client() as client:
        confirm_data = {
            'shot_id': anime_id
        }
        response = client.post(
            '/rest/v1/anime/confirm',
            data=json.dumps(confirm_data),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Confirm anime failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert result['data']['status'] == 'confirmed', f"Status should be 'confirmed': {result}"

        print(f"  Confirmed anime: {anime_id}")
        return anime_id


def test_get_anime_details():
    """测试获取动画镜头详情接口（包含 video/picture assets）"""
    app = create_app()

    # 先创建作品和镜头
    with app.test_client() as client:
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Details',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        anime_data = {
            'work_id': work_id,
            'author_id': TEST_AUTHOR_ID,
            'anime_number': 1,
            'description': 'Test shot with details',
            'notes': 'Test notes'
        }
        create_response = client.post(
            '/rest/v1/anime/createAnime',
            data=json.dumps(anime_data),
            content_type='application/json'
        )
        anime_id = json.loads(create_response.data)['data']['anime_id']

    # 测试获取详情
    with app.test_client() as client:
        response = client.get(f'/rest/v1/anime/getVideoDetails?shot_id={anime_id}')

        assert response.status_code == 200, f"Get anime details failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert result['data']['anime_id'] == anime_id, f"Anime ID mismatch: {result}"
        assert 'asset_ids' in result['data'], f"Response should contain asset_ids: {result}"

        print(f"  Retrieved anime details: {anime_id}")


def test_anime_health_check():
    """测试动画服务健康检查"""
    app = create_app()

    with app.test_client() as client:
        response = client.get('/rest/v1/anime/health')

        assert response.status_code == 200, f"Health check failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success'
        assert result['data']['status'] == 'ok'

        print("  Anime service health check passed")


# ==================== Picture 上传测试 ====================
# 注意：以下测试需要配置阿里云 OSS 才能运行
# 需要配置环境变量：ALIYUN_OSS_ENDPOINT, ALIYUN_OSS_ACCESS_KEY_ID, ALIYUN_OSS_ACCESS_KEY_SECRET, ALIYUN_OSS_BUCKET_NAME


def _skip_picture_test_if_needed():
    """如果 OSS 未配置，跳过图片测试"""
    import os
    endpoint = os.getenv('ALIYUN_OSS_ENDPOINT', '')
    access_key = os.getenv('ALIYUN_OSS_ACCESS_KEY_ID', '')
    # 如果 access_key 是默认值或为空，则认为未配置
    if not endpoint or not access_key or access_key == 'xxxxx':
        print(f"  SKIPPED: OSS not configured (requires ALIYUN_OSS_ACCESS_KEY_ID)")
        return True

    # 检查 pics 文件夹是否存在
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pics_dir = os.path.join(base_dir, 'pics')
    if not os.path.exists(pics_dir):
        print(f"  SKIPPED: pics directory not found")
        return True

    import glob
    jpg_files = glob.glob(os.path.join(pics_dir, '*.jpg'))
    if not jpg_files:
        print(f"  SKIPPED: No .jpg files found in pics directory")
        return True

    return False


def test_upload_picture():
    """测试图片上传接口"""
    # 检查是否需要跳过
    if _skip_picture_test_if_needed():
        return None

    app = create_app()

    # 检查 pics 文件夹，获取测试图片
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_image_path = None
    import glob
    pics_dir = os.path.join(base_dir, 'pics')
    jpg_files = glob.glob(os.path.join(pics_dir, '*.jpg'))
    if jpg_files:
        test_image_path = jpg_files[0]

    if not test_image_path:
        print(f"  SKIPPED: No test image file found")
        return None

    with app.test_client() as client:
        # 先创建一个作品
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Picture',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        # 上传测试图片
        from werkzeug.datastructures import FileStorage
        with open(test_image_path, 'rb') as f:
            file_storage = FileStorage(f, filename=os.path.basename(test_image_path))
            data = {
                'picture': file_storage,
                'user_id': TEST_USER_ID,
                'work_id': work_id
            }
            response = client.post(
                '/rest/v1/picture/uploadPicture',
                data=data,
                content_type='multipart/form-data'
            )

        assert response.status_code == 200, f"Upload picture failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert 'asset_id' in result['data'], f"Response should contain asset_id: {result}"
        assert 'url' in result['data'], f"Response should contain url: {result}"

        asset_id = result['data']['asset_id']
        print(f"  Uploaded picture: {asset_id}")
        return asset_id, work_id


def test_get_picture_by_asset_id():
    """测试根据资产 ID 获取图片接口"""
    # 检查是否需要跳过
    if _skip_picture_test_if_needed():
        return

    app = create_app()

    # 获取测试图片
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_image_path = None
    import glob
    pics_dir = os.path.join(base_dir, 'pics')
    jpg_files = glob.glob(os.path.join(pics_dir, '*.jpg'))
    if len(jpg_files) > 1:
        test_image_path = jpg_files[1]

    if not test_image_path:
        print(f"  SKIPPED: No test image file found")
        return

    with app.test_client() as client:
        # 先创建一个作品
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Get Picture',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        # 上传测试图片
        from werkzeug.datastructures import FileStorage
        with open(test_image_path, 'rb') as f:
            file_storage = FileStorage(f, filename=os.path.basename(test_image_path))
            upload_data = {
                'picture': file_storage,
                'user_id': TEST_USER_ID,
                'work_id': work_id
            }
            upload_response = client.post(
                '/rest/v1/picture/uploadPicture',
                data=upload_data,
                content_type='multipart/form-data'
            )
            asset_id = json.loads(upload_response.data)['data']['asset_id']

        # 测试获取图片
        response = client.get(f'/rest/v1/picture/fetchPictureByAssetId?asset_id={asset_id}&user_id={TEST_USER_ID}')

        assert response.status_code == 200, f"Get picture failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert result['data']['asset']['asset_id'] == asset_id, f"Asset ID mismatch: {result}"

        print(f"  Retrieved picture: {asset_id}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Starting Novel & Anime API Tests")
    print("=" * 50)

    tests = [
        # Novel 模块
        ("Create Novel", test_create_novel),
        ("Get Novel By Work ID", test_get_novel_by_work_id),
        ("Update Novel", test_update_novel),
        ("Delete Novel", test_delete_novel),
        # Anime 模块
        ("Create Anime", test_create_anime),
        ("Get Animes By Work ID", test_get_animes_by_work_id),
        ("Confirm Anime", test_confirm_anime),
        ("Get Anime Details", test_get_anime_details),
        ("Anime Health Check", test_anime_health_check),
        # Picture 模块
        ("Upload Picture", test_upload_picture),
        ("Get Picture By Asset ID", test_get_picture_by_asset_id),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test_name, test_func in tests:
        print(f"\n[{test_name}]")

        # 图片测试需要特殊处理跳过逻辑
        if test_name in ["Upload Picture", "Get Picture By Asset ID"]:
            if _skip_picture_test_if_needed():
                skipped += 1
                continue

        try:
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
    print(f"Tests completed: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 50)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
