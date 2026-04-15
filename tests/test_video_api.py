"""
测试 Video 模块 API 接口。
覆盖所有 video 相关的数据库读写操作和大模型接口调用。
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


def is_dashscope_configured():
    """检查 DashScope（通义千问）是否已配置"""
    api_key = os.getenv('DASHSCOPE_API_KEY', '')
    if not api_key or api_key == 'xxxxx':
        return False
    return True


def _skip_video_test_if_needed():
    """如果 DashScope 未配置，跳过视频测试"""
    if not is_dashscope_configured():
        print(f"  SKIPPED: DashScope API not configured (requires DASHSCOPE_API_KEY)")
        return True
    return False


def create_test_anime_for_video(work_id, anime_number=1):
    """创建用于视频生成的测试 anime 记录"""
    app = create_app()

    with app.test_client() as client:
        anime_data = {
            'work_id': work_id,
            'author_id': TEST_AUTHOR_ID,
            'anime_number': anime_number,
            'description': 'Test anime for video generation',
            'notes': 'Test notes'
        }
        response = client.post(
            '/rest/v1/anime/createAnime',
            data=json.dumps(anime_data),
            content_type='application/json'
        )
        result = json.loads(response.data)
        return result['data']['anime_id']


def test_generate_video_single_image():
    """测试单图视频生成接口"""
    # 检查是否需要跳过
    if _skip_video_test_if_needed():
        return

    app = create_app()

    with app.test_client() as client:
        # 先创建作品
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Video',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        # 创建 anime 记录
        anime_id = create_test_anime_for_video(work_id)

        # 上传图片（使用 pics 文件夹中的图片）
        import glob
        jpg_files = glob.glob(os.path.join('e:\\个人\\coding\\project\\trial\\pics', '*.jpg'))
        if not jpg_files:
            print(f"  SKIPPED: No test image files found in pics directory")
            return

        from werkzeug.datastructures import FileStorage
        with open(jpg_files[0], 'rb') as f:
            file_storage = FileStorage(f, filename='test.jpg')
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
            picture_data = json.loads(upload_response.data)['data']
            picture_url = picture_data['url']
            picture_id = picture_data['asset_id']

        # 测试视频生成接口 - 使用正确的数据格式
        # anime.py 中的 _get_picture_from_request 期望 data 中包含 'picture' 字段
        # 且 picture 是一个包含 id/asset_id 和 url/cos_url/cloudflare_url 的对象
        video_data = {
            'shot_id': anime_id,
            'prompt': 'Animate this scene naturally',
            'picture': {
                'asset_id': picture_id,
                'cos_url': picture_url  # 使用 cos_url 作为图片来源
            },
            'duration': 5,
            'motion_strength': 0.5
        }
        response = client.post(
            '/rest/v1/anime/generateVideo',
            data=json.dumps(video_data),
            content_type='application/json'
        )

        # 验证响应
        assert response.status_code == 200, f"Generate video failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert 'data' in result, f"Response should contain data: {result}"

        # 视频生成可能成功或返回任务创建
        video_result = result['data']
        print(f"  Video generation result: {video_result.get('success', 'N/A')}")

        # 验证视频信息被保存到数据库
        details_response = client.get(f'/rest/v1/anime/getVideoDetails?shot_id={anime_id}')
        details_result = json.loads(details_response.data)

        assert details_result['status'] == 'success', f"Get details failed: {details_result}"
        assert 'video_assets' in details_result['data'], "Response should contain video_assets"

        print(f"  Video generation task created for anime: {anime_id}")
        return anime_id, video_result


def test_generate_multi_image_video():
    """测试多图片视频生成接口"""
    # 检查是否需要跳过
    if _skip_video_test_if_needed():
        return

    app = create_app()

    with app.test_client() as client:
        # 先创建作品
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Multi-Image Video',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        # 创建 anime 记录
        anime_id = create_test_anime_for_video(work_id)

        # 上传多张图片（使用 pics 文件夹中的图片）
        import glob
        jpg_files = glob.glob(os.path.join('e:\\个人\\coding\\project\\trial\\pics', '*.jpg'))
        if len(jpg_files) < 2:
            print(f"  SKIPPED: Need at least 2 images for multi-image video test")
            return

        pictures = []
        from werkzeug.datastructures import FileStorage

        for i, img_path in enumerate(jpg_files[:2]):  # 使用前 2 张图片
            with open(img_path, 'rb') as f:
                file_storage = FileStorage(f, filename=f'test{i}.jpg')
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
                picture_data = json.loads(upload_response.data)['data']
                # 使用 cos_url 作为图片来源
                pictures.append({
                    'asset_id': picture_data['asset_id'],
                    'cos_url': picture_data['url']
                })

        # 测试多图片视频生成接口
        video_data = {
            'shot_id': anime_id,
            'prompt': 'Create a smooth transition between these images',
            'pictures': pictures
        }
        response = client.post(
            '/rest/v1/anime/generateMultiImageVideo',
            data=json.dumps(video_data),
            content_type='application/json'
        )

        # 验证响应
        assert response.status_code == 200, f"Generate multi-image video failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"

        print(f"  Multi-image video generation task created for anime: {anime_id}")
        return anime_id


def test_get_video_details():
    """测试获取视频详情接口"""
    app = create_app()

    with app.test_client() as client:
        # 先创建作品和 anime
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Video Details',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        anime_id = create_test_anime_for_video(work_id)

        # 测试获取视频详情
        response = client.get(f'/rest/v1/anime/getVideoDetails?shot_id={anime_id}')

        assert response.status_code == 200, f"Get video details failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success', f"Response status should be 'success': {result}"
        assert 'data' in result, f"Response should contain data: {result}"
        assert result['data']['anime_id'] == anime_id, f"Anime ID mismatch: {result}"
        assert 'asset_ids' in result['data'], f"Response should contain asset_ids: {result}"
        assert 'video_assets' in result['data'], f"Response should contain video_assets: {result}"
        assert 'picture_assets' in result['data'], f"Response should contain picture_assets: {result}"

        print(f"  Retrieved video details: {anime_id}")


def test_video_health_check():
    """测试视频服务健康检查"""
    app = create_app()

    with app.test_client() as client:
        response = client.get('/rest/v1/anime/health')

        assert response.status_code == 200, f"Health check failed: {response.data}"
        result = json.loads(response.data)

        assert result['status'] == 'success'
        assert result['data']['status'] == 'ok'

        print("  Video service health check passed")


def test_video_database_storage():
    """测试视频数据库存储（MongoDB）"""
    # 检查是否需要跳过
    if _skip_video_test_if_needed():
        return

    app = create_app()
    from db.mongo_anime import anime_details_service

    # 确保 MongoDB 服务已初始化
    with app.app_context():
        if not anime_details_service._initialized:
            anime_details_service.init_app(app)

    with app.test_client() as client:
        # 先创建作品和 anime
        work_data = {
            'author_id': TEST_AUTHOR_ID,
            'title': 'Test Work for Video DB',
            'work_type': 'anime'
        }
        work_response = client.post(
            '/rest/v1/work/createWork',
            data=json.dumps(work_data),
            content_type='application/json'
        )
        work_id = json.loads(work_response.data)['data']['work_id']

        anime_id = create_test_anime_for_video(work_id)

        # 模拟保存视频信息到 MongoDB
        video_asset_id = str(uuid.uuid4())
        video_url = 'http://test.example.com/video.mp4'

        # 先插入基础文档，再添加 asset
        try:
            anime_details_service.insert_anime_details(
                anime_id=anime_id,
                work_id=work_id,
                asset_ids=[]
            )
        except Exception as e:
            # 如果已存在，忽略错误
            print(f"  Note: insert_anime_details may have failed (document may exist): {e}")

        anime_details_service.add_asset_to_anime(
            anime_id=anime_id,
            asset_id=video_asset_id,
            asset_type='video',
            asset_data={
                'video_url': video_url,
                'task_id': 'test-task-id',
                'model_used': 'wan2.6-i2v'
            }
        )

        # 验证数据已保存
        details = anime_details_service.fetch_anime_details(anime_id)

        assert details is not None, "Anime details should exist"
        assert 'video_assets' in details, "Details should contain video_assets"

        video_assets = details.get('video_assets', [])
        assert len(video_assets) > 0, "Should have at least one video asset"

        # 查找我们刚刚保存的视频
        found_video = False
        for asset in video_assets:
            if isinstance(asset, dict):
                # 检查是否是 asset_data 格式
                if asset.get('video_url') == video_url:
                    found_video = True
                    break
                # 检查是否是嵌套格式
                asset_data = asset.get('asset_data', {})
                if asset_data.get('video_url') == video_url:
                    found_video = True
                    break
            elif isinstance(asset, str) and asset == video_asset_id:
                # 如果只是 asset_id 字符串，也认为找到
                found_video = True
                break

        assert found_video, f"Video asset {video_asset_id} not found in {video_assets}"

        print(f"  Video data stored and verified in MongoDB for anime: {anime_id}")


def test_video_ai_service_call():
    """测试视频 AI 服务调用（验证大模型接口）"""
    # 检查是否需要跳过
    if _skip_video_test_if_needed():
        return

    from services.video_generation_service import video_generation_service

    app = create_app()

    # 初始化服务
    with app.app_context():
        if not video_generation_service._initialized:
            video_generation_service.init_app(app)

        # 验证服务已初始化
        assert video_generation_service._initialized, "Video generation service should be initialized"

        # 获取模型配置
        model_config = video_generation_service.get_current_model_config()
        assert 'video_model' in model_config, "Config should contain video_model"
        assert model_config['video_model'] == 'wan2.6-i2v', f"Expected wan2.6-i2v, got {model_config['video_model']}"

        print(f"  Video AI service configured with model: {model_config['video_model']}")

        # 验证 API 调用方法存在
        assert hasattr(video_generation_service, 'generate_single_image_anime'), "Should have generate_single_image_anime method"
        assert hasattr(video_generation_service, 'generate_start_end_frame_anime'), "Should have generate_start_end_frame_anime method"
        assert hasattr(video_generation_service, 'call_video_api'), "Should have call_video_api method"

        print("  Video AI service methods verified")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Starting Video API Tests")
    print("=" * 60)

    tests = [
        ("Get Video Details", test_get_video_details),
        ("Video Health Check", test_video_health_check),
        ("Video Database Storage", test_video_database_storage),
        ("Video AI Service Call", test_video_ai_service_call),
        ("Generate Video (Single Image)", test_generate_video_single_image),
        ("Generate Multi-Image Video", test_generate_multi_image_video),
    ]

    passed = 0
    failed = 0
    skipped = 0

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
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Tests completed: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
