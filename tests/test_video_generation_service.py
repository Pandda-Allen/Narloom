"""
测试视频生成服务类。
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock, PropertyMock
import pytest
from services.video_generation_service import VideoGenerationService, video_generation_service


class TestVideoGenerationService:
    """测试视频生成服务类"""

    @patch('services.video_generation_service.qwen_ai_service')
    def test_singleton_pattern(self, mock_qwen):
        """测试单例模式"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        from flask import Flask
        app = Flask(__name__)
        app.config['DASHSCOPE_API_KEY'] = 'test_key'

        instance1 = VideoGenerationService()
        instance2 = VideoGenerationService()
        assert instance1 is instance2, "VideoGenerationService should be a singleton"
        print("OK Singleton pattern test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    def test_get_current_model_config(self, mock_qwen):
        """测试获取当前模型配置"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        service = VideoGenerationService()
        config = service.get_current_model_config()

        assert config is not None
        assert "vision_model" in config
        assert "video_model" in config
        assert "panel_detect_model" in config
        assert config["vision_model"] == "qwen-vl-max"
        assert config["video_model"] == "wanx2.0-t2v"
        assert config["panel_detect_model"] == "qwen-vl-max"
        print("OK Get current model config test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    def test_set_model_config(self, mock_qwen):
        """测试设置模型配置"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        service = VideoGenerationService()

        # 测试更新单个模型
        config = service.set_model_config(vision_model="qwen-vl-plus")
        assert config["vision_model"] == "qwen-vl-plus"
        assert config["video_model"] == "wanx2.0-t2v"  # 保持不变

        # 测试更新多个模型
        config = service.set_model_config(
            video_model="wanx2.0-t2v-advanced",
            panel_detect_model="qwen-vl-max-latest"
        )
        assert config["video_model"] == "wanx2.0-t2v-advanced"
        assert config["panel_detect_model"] == "qwen-vl-max-latest"

        # 测试全部更新
        config = service.set_model_config(
            vision_model="qwen-vl-max",
            video_model="wanx2.0-t2v",
            panel_detect_model="qwen-vl-max"
        )
        assert config["vision_model"] == "qwen-vl-max"
        assert config["video_model"] == "wanx2.0-t2v"
        assert config["panel_detect_model"] == "qwen-vl-max"

        print("OK Set model config test passed")


class TestComicImageAnalysis:
    """测试漫画图片分析功能"""

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_analyze_comic_image_success(self, mock_post, mock_qwen):
        """测试分析漫画图片成功"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        # Mock API 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": '{"panels": [{"index": 1, "bbox": [10, 10, 200, 150], "description": "角色 A"}], "scene": "雨天"}'
            }
        }
        mock_post.return_value = mock_response

        service = VideoGenerationService()
        result = service.analyze_comic_image("https://example.com/image.jpg")

        assert result["success"] is True
        assert "analysis" in result
        assert result["model_used"] == "qwen-vl-max"
        print("OK Analyze comic image success test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_analyze_comic_image_with_history(self, mock_post, mock_qwen):
        """测试带历史对话的图片分析"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"text": '{"panels": [], "scene": "场景"}'
            }
        }
        mock_post.return_value = mock_response

        service = VideoGenerationService()
        history = [
            {"role": "user", "content": "分析这张图"},
            {"role": "assistant", "content": "好的"}
        ]
        result = service.analyze_comic_image("https://example.com/image.jpg", history)

        assert result["success"] is True
        # 验证历史对话被传递
        assert mock_post.called
        print("OK Analyze comic image with history test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_analyze_comic_image_failure(self, mock_post, mock_qwen):
        """测试分析漫画图片失败"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        mock_post.side_effect = Exception("API Error")

        service = VideoGenerationService()
        result = service.analyze_comic_image("https://example.com/image.jpg")

        assert result["success"] is False
        assert "error" in result
        assert result["model_used"] == "qwen-vl-max"
        print("OK Analyze comic image failure test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_detect_comic_panels_success(self, mock_post, mock_qwen):
        """测试检测漫画分格成功"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": '{"panels": [{"index": 1, "bbox": [10, 10, 200, 150], "description": "分格 1"}]}'
            }
        }
        mock_post.return_value = mock_response

        service = VideoGenerationService()
        result = service.detect_comic_panels("https://example.com/image.jpg")

        assert result["success"] is True
        assert "panels" in result
        assert len(result["panels"]) == 1
        assert result["model_used"] == "qwen-vl-max"
        print("OK Detect comic panels success test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_detect_comic_panels_empty(self, mock_post, mock_qwen):
        """测试检测漫画分格但无分格"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {"text": '{"panels": []}'}
        }
        mock_post.return_value = mock_response

        service = VideoGenerationService()
        result = service.detect_comic_panels("https://example.com/image.jpg")

        assert result["success"] is True
        assert result["panels"] == []
        print("OK Detect comic panels empty test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_detect_comic_panels_failure(self, mock_post, mock_qwen):
        """测试检测漫画分格失败"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        mock_post.side_effect = Exception("API Error")

        service = VideoGenerationService()
        result = service.detect_comic_panels("https://example.com/image.jpg")

        assert result["success"] is False
        assert "error" in result
        assert result["panels"] == []
        print("OK Detect comic panels failure test passed")


class TestVideoGeneration:
    """测试视频生成功能"""

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.get')
    @patch('services.video_generation_service.requests.post')
    @patch('services.video_generation_service.time.sleep', return_value=None)
    def test_generate_panel_animation_success(self, mock_sleep, mock_post, mock_get, mock_qwen):
        """测试生成单分格动画成功"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        # Mock 视频生成 API 响应 - 提交任务
        submit_response = MagicMock()
        submit_response.status_code = 200
        submit_response.json.return_value = {"task_id": "task_123"}
        mock_post.return_value = submit_response

        # Mock 任务状态查询 - 第一次返回 pending，第二次返回 succeeded
        status_pending = MagicMock()
        status_pending.status_code = 200
        status_pending.json.return_value = {"status": "pending"}

        status_succeeded = MagicMock()
        status_succeeded.status_code = 200
        status_succeeded.json.return_value = {
            "status": "succeeded",
            "output": {"video_url": "https://video.mp4", "preview_url": "https://preview.gif"}
        }

        mock_get.side_effect = [status_pending, status_succeeded]

        service = VideoGenerationService()
        result = service.generate_panel_animation(
            image_url="https://example.com/image.jpg",
            panel_bbox=[10, 10, 200, 150],
            prompt="微风吹过",
            duration=3,
            motion_strength=0.5
        )

        assert result["success"] is True
        assert "video_url" in result
        assert result["duration"] == 3
        assert result["model_used"] == "wanx2.0-t2v"
        print("OK Generate panel animation success test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_generate_panel_animation_api_error(self, mock_post, mock_qwen):
        """测试生成单分格动画 API 错误"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        mock_post.return_value = MagicMock(status_code=500)

        service = VideoGenerationService()
        result = service.generate_panel_animation(
            image_url="https://example.com/image.jpg",
            panel_bbox=[10, 10, 200, 150],
            prompt="微风吹过"
        )

        assert result["success"] is False
        assert "error" in result
        print("OK Generate panel animation API error test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.get')
    @patch('services.video_generation_service.requests.post')
    @patch('services.video_generation_service.time.sleep', return_value=None)
    def test_generate_multi_panel_anime_success(self, mock_sleep, mock_post, mock_get, mock_qwen):
        """测试生成多分格动画成功"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        panels = [
            {"index": 1, "bbox": [10, 10, 200, 150], "description": "分格 1"},
            {"index": 2, "bbox": [210, 10, 400, 150], "description": "分格 2"}
        ]
        prompts = ["提示词 1", "提示词 2"]

        # Mock 提交任务响应
        submit_responses = []
        for i in range(2):
            submit_response = MagicMock()
            submit_response.status_code = 200
            submit_response.json.return_value = {"task_id": f"task_{i}"}
            submit_responses.append(submit_response)
        mock_post.side_effect = submit_responses

        # Mock 任务状态查询 - 每个任务需要 pending + succeeded
        get_responses = []
        for i in range(2):
            status_pending = MagicMock()
            status_pending.status_code = 200
            status_pending.json.return_value = {"status": "pending"}
            get_responses.append(status_pending)

            status_succeeded = MagicMock()
            status_succeeded.status_code = 200
            status_succeeded.json.return_value = {
                "status": "succeeded",
                "output": {"video_url": f"https://video{i}.mp4", "preview_url": f"https://preview{i}.gif"}
            }
            get_responses.append(status_succeeded)
        mock_get.side_effect = get_responses

        service = VideoGenerationService()
        result = service.generate_multi_panel_anime(
            image_url="https://example.com/image.jpg",
            panels=panels,
            prompts=prompts,
            transition_style="smooth"
        )

        assert result["success"] is True
        assert "video_url" in result
        assert result["panel_count"] == 2
        assert result["transition_style"] == "smooth"
        print("OK Generate multi panel anime success test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    def test_generate_multi_panel_anime_no_bbox(self, mock_qwen):
        """测试生成多分格动画但分格无 bbox"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        panels = [
            {"index": 1, "description": "分格 1"}  # 没有 bbox
        ]
        prompts = ["提示词 1"]

        service = VideoGenerationService()
        result = service.generate_multi_panel_anime(
            image_url="https://example.com/image.jpg",
            panels=panels,
            prompts=prompts
        )

        assert result["success"] is False
        assert result["error"] == "No panels were successfully generated"
        print("OK Generate multi panel anime no bbox test passed")


class TestConversationHistory:
    """测试对话历史管理功能"""

    @patch('services.video_generation_service.qwen_ai_service')
    def test_manage_conversation_history_no_summary(self, mock_qwen):
        """测试对话历史管理（不需要总结）"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True
        mock_qwen.process_request.return_value = {"success": True, "result": "总结"}

        service = VideoGenerationService()
        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮助你的？"}
        ]
        new_message = {"role": "user", "content": "我想分析这张图"}

        updated_history, summary = service.manage_conversation_history(
            session_id="test_session",
            new_message=new_message,
            history=history,
            max_turns=10,
            summary_threshold=5
        )

        assert len(updated_history) == 3
        assert summary is None
        print("OK Manage conversation history no summary test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    def test_manage_conversation_history_with_summary(self, mock_qwen):
        """测试对话历史管理（需要总结）"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True
        mock_qwen.process_request.return_value = {"success": True, "result": "对话总结"}

        from flask import Flask
        app = Flask(__name__)
        app.config['DASHSCOPE_API_KEY'] = 'test_key'

        service = VideoGenerationService()

        # 创建超过阈值的历史
        history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"消息{i}"} for i in range(10)]
        new_message = {"role": "user", "content": "新消息"}

        with app.app_context():
            updated_history, summary = service.manage_conversation_history(
                session_id="test_session",
                new_message=new_message,
                history=history,
                max_turns=10,
                summary_threshold=5
            )

        assert summary is not None
        # 应该包含系统消息（总结）+ 最近的轮次
        assert len(updated_history) <= 6  # 系统消息 + 5 条最近消息
        print("OK Manage conversation history with summary test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    def test_summarize_conversation_success(self, mock_qwen):
        """测试总结对话成功"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True
        mock_qwen.process_request.return_value = {"success": True, "result": "对话总结内容"}

        service = VideoGenerationService()
        messages = [
            {"role": "user", "content": "我想分析这张漫画图"},
            {"role": "assistant", "content": "好的，我来帮你分析"}
        ]

        summary = service._summarize_conversation(messages)

        assert summary is not None
        assert mock_qwen.process_request.called
        print("OK Summarize conversation success test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    def test_summarize_conversation_failure(self, mock_qwen):
        """测试总结对话失败"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True
        mock_qwen.process_request.return_value = {"success": False, "error": "API 错误"}

        service = VideoGenerationService()
        messages = [{"role": "user", "content": "消息"}]

        summary = service._summarize_conversation(messages)

        assert summary == "对话总结失败"
        print("OK Summarize conversation failure test passed")


class TestHelperMethods:
    """测试辅助方法"""

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_call_vision_model_without_json(self, mock_post, mock_qwen):
        """测试调用视觉模型（不期望 JSON 响应）"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"text": "分析结果"}}
        mock_post.return_value = mock_response

        service = VideoGenerationService()
        result = service._call_vision_model(
            model="qwen-vl-max",
            system_prompt="分析图片",
            image_url="https://example.com/image.jpg",
            expect_json=False
        )

        assert result == "分析结果"
        print("OK Call vision model without JSON test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_call_vision_model_with_json(self, mock_post, mock_qwen):
        """测试调用视觉模型（期望 JSON 响应）"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"output": {"text": '{"key": "value"}'}}
        mock_post.return_value = mock_response

        service = VideoGenerationService()
        result = service._call_vision_model(
            model="qwen-vl-max",
            system_prompt="分析图片",
            image_url="https://example.com/image.jpg",
            expect_json=True
        )

        assert isinstance(result, dict)
        assert result["key"] == "value"
        print("OK Call vision model with JSON test passed")

    @patch('services.video_generation_service.qwen_ai_service')
    @patch('services.video_generation_service.requests.post')
    def test_call_vision_model_api_error(self, mock_post, mock_qwen):
        """测试调用视觉模型 API 错误"""
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        service = VideoGenerationService()

        with pytest.raises(Exception) as exc_info:
            service._call_vision_model(
                model="qwen-vl-max",
                system_prompt="分析图片",
                image_url="https://example.com/image.jpg"
            )

        assert "Vision API error" in str(exc_info.value)
        print("OK Call vision model API error test passed")

    def test_crop_image_region_oss_url(self):
        """测试裁剪图片区域（OSS URL）"""
        service = VideoGenerationService()

        image_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/comic/image.jpg"
        bbox = [100, 100, 300, 250]

        result = service._crop_image_region(image_url, bbox)

        assert "x-oss-process=image/crop" in result
        assert "x_100" in result
        assert "y_100" in result
        assert "w_200" in result
        assert "h_150" in result
        print("OK Crop image region OSS URL test passed")

    def test_crop_image_region_non_oss_url(self):
        """测试裁剪图片区域（非 OSS URL）"""
        service = VideoGenerationService()

        image_url = "https://example.com/image.jpg"
        bbox = [100, 100, 300, 250]

        result = service._crop_image_region(image_url, bbox)

        # 非 OSS URL 直接返回原 URL
        assert result == image_url
        print("OK Crop image region non-OSS URL test passed")

    def test_crop_image_region_with_query_params(self):
        """测试裁剪图片区域（带查询参数的 OSS URL）"""
        service = VideoGenerationService()

        image_url = "https://bucket.oss-cn-hangzhou.aliyuncs.com/comic/image.jpg?x-oss-process=resize,w_100"
        bbox = [100, 100, 300, 250]

        result = service._crop_image_region(image_url, bbox)

        # 应该使用 & 连接
        assert "&x-oss-process=image/crop" in result
        print("OK Crop image region with query params test passed")

    def test_stitch_videos(self):
        """测试拼接视频片段"""
        service = VideoGenerationService()

        videos = [
            {"video_url": "https://video1.mp4", "preview_url": "https://preview1.gif"},
            {"video_url": "https://video2.mp4", "preview_url": "https://preview2.gif"}
        ]

        result = service._stitch_videos(videos, "smooth")

        assert result["video_url"] == "https://video1.mp4"
        assert result["preview_url"] == "https://preview1.gif"
        assert result["duration"] == 6  # 2 个视频 * 3 秒
        print("OK Stitch videos test passed")

    def test_stitch_videos_empty_list(self):
        """测试拼接空视频列表"""
        service = VideoGenerationService()

        videos = []

        with pytest.raises(IndexError):
            service._stitch_videos(videos, "smooth")
        print("OK Stitch videos empty list test passed (expected IndexError)")


def run_all_tests():
    """运行所有测试"""
    print("\n=== Running Video Generation Service Tests ===\n")

    # 单例模式测试
    test_singleton = TestVideoGenerationService()
    with patch('services.video_generation_service.qwen_ai_service') as mock_qwen:
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True
        test_singleton.test_singleton_pattern(mock_qwen)

    # 模型配置测试
    test_model_config = TestVideoGenerationService()
    with patch('services.video_generation_service.qwen_ai_service') as mock_qwen:
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True
        test_model_config.test_get_current_model_config(mock_qwen)
        test_model_config.test_set_model_config(mock_qwen)

    # 漫画分析测试
    test_analysis = TestComicImageAnalysis()
    with patch('services.video_generation_service.qwen_ai_service') as mock_qwen:
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True
        with patch('services.video_generation_service.requests.post') as mock_post:
            test_analysis.test_analyze_comic_image_success(mock_post, mock_qwen)
            test_analysis.test_analyze_comic_image_with_history(mock_post, mock_qwen)
            test_analysis.test_detect_comic_panels_success(mock_post, mock_qwen)
            test_analysis.test_detect_comic_panels_empty(mock_post, mock_qwen)

    # 视频生成测试
    test_generation = TestVideoGeneration()
    with patch('services.video_generation_service.qwen_ai_service') as mock_qwen:
        mock_qwen.api_key = 'test_key'
        mock_qwen._initialized = True
        with patch('services.video_generation_service.requests.post') as mock_post:
            test_generation.test_generate_multi_panel_anime_no_bbox(mock_qwen)

    # 辅助方法测试
    test_helpers = TestHelperMethods()
    test_helpers.test_crop_image_region_oss_url()
    test_helpers.test_crop_image_region_non_oss_url()
    test_helpers.test_stitch_videos()

    print("\n=== All Video Generation Service Tests Completed ===\n")


if __name__ == '__main__':
    run_all_tests()
