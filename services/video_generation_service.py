"""
视频生成服务类
负责漫画图片识别、分格检测、动态图像生成等功能
"""
import os
import json
import requests
import base64
from typing import Dict, Any, List, Optional, Tuple
from flask import current_app, stream_with_context, Response
from datetime import datetime
import uuid
import time

from .ai_service import qwen_ai_service


class VideoGenerationService:
    """视频生成服务类"""

    _instance = None
    _initialized = False
    _api_key = None
    _api_base = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_app(self, app):
        with app.app_context():
            self._initialize()

    def _initialize(self):
        if self._initialized:
            return

        # 使用与 Qwen AI 相同的配置
        self._api_key = qwen_ai_service.api_key
        self._api_base = "https://dashscope.aliyuncs.com/api/v1"
        self._initialized = True

    # ==================== 模型配置管理 ====================
    def get_current_model_config(self) -> Dict[str, Any]:
        """获取当前使用的模型配置"""
        # 默认使用通义万相进行视频生成
        return {
            "vision_model": "qwen-vl-max",      # 视觉理解模型
            "video_model": "wanx2.0-t2v",        # 视频生成模型
            "panel_detect_model": "qwen-vl-max"  # 分格检测模型
        }

    def set_model_config(self, vision_model: str = None, video_model: str = None, panel_detect_model: str = None):
        """
        动态设置模型配置

        Args:
            vision_model: 视觉理解模型
            video_model: 视频生成模型
            panel_detect_model: 分格检测模型
        """
        config = self.get_current_model_config()
        if vision_model:
            config["vision_model"] = vision_model
        if video_model:
            config["video_model"] = video_model
        if panel_detect_model:
            config["panel_detect_model"] = panel_detect_model
        return config

    # ==================== 漫画图片识别与分析 ====================
    def analyze_comic_image(self, image_url: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        分析漫画图片内容

        Args:
            image_url: 图片 URL
            conversation_history: 历史对话内容

        Returns:
            Dict: 分析结果，包括分格信息、内容描述等
        """
        model_config = self.get_current_model_config()
        vision_model = model_config["vision_model"]

        # 构建系统提示词
        system_prompt = """你是一位专业的漫画分析专家。请分析这张漫画图片，并提供以下信息：

1. 分格检测：识别漫画中的所有分格（panel），按照从左上到右下的顺序编号
2. 每个分格的详细描述：
   - 分格位置（边界框坐标）
   - 分格中的画面内容
   - 分格中的人物和动作
   - 分格中的文字内容（如果有）
3. 整体场景描述
4. 建议的动态化方向：如何让静态画面产生自然的动态效果

请以 JSON 格式返回分析结果。"""

        # 如果有历史对话，添加到上下文中
        context_messages = []
        if conversation_history:
            for msg in conversation_history[-5:]:  # 只保留最近 5 轮
                context_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })

        # 调用视觉模型
        try:
            result = self._call_vision_model(
                model=vision_model,
                system_prompt=system_prompt,
                image_url=image_url,
                context=context_messages
            )
            return {
                "success": True,
                "analysis": result,
                "model_used": vision_model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_used": vision_model
            }

    def detect_comic_panels(self, image_url: str) -> Dict[str, Any]:
        """
        检测漫画分格

        Args:
            image_url: 图片 URL

        Returns:
            Dict: 分格检测结果
        """
        model_config = self.get_current_model_config()
        panel_model = model_config["panel_detect_model"]

        system_prompt = """请检测这张漫画图片中的所有分格，返回每个分格的边界框坐标（bbox_2d 格式：[x1, y1, x2, y2]）。
按照从左上到右下的顺序排列分格。
只返回 JSON 数组，格式为：{"panels": [{"index": 1, "bbox": [x1, y1, x2, y2], "description": "分格内容简述"}, ...]}"""

        try:
            result = self._call_vision_model(
                model=panel_model,
                system_prompt=system_prompt,
                image_url=image_url,
                expect_json=True
            )
            return {
                "success": True,
                "panels": result.get("panels", []),
                "model_used": panel_model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "panels": []
            }

    # ==================== 视频生成 ====================
    def generate_panel_animation(self,
                                  image_url: str,
                                  panel_bbox: List[int],
                                  prompt: str,
                                  duration: int = 3,
                                  motion_strength: float = 0.5) -> Dict[str, Any]:
        """
        为单个分格生成动态动画

        Args:
            image_url: 图片 URL
            panel_bbox: 分格边界框 [x1, y1, x2, y2]
            prompt: 动画生成提示词
            duration: 视频时长（秒）
            motion_strength: 运动强度 0-1

        Returns:
            Dict: 生成的视频信息（临时 URL，不保存）
        """
        model_config = self.get_current_model_config()
        video_model = model_config["video_model"]

        # 裁剪分格区域（通过后端处理）
        cropped_image_url = self._crop_image_region(image_url, panel_bbox)

        # 构建视频生成请求
        payload = {
            "model": video_model,
            "input": {
                "image": cropped_image_url,
                "prompt": prompt
            },
            "parameters": {
                "duration": duration,
                "motion_strength": motion_strength,
                "resolution": "720p"
            }
        }

        try:
            # 调用视频生成 API
            video_result = self._call_video_generation_api(payload)

            if video_result.get("success"):
                return {
                    "success": True,
                    "video_url": video_result.get("video_url"),
                    "preview_url": video_result.get("preview_url"),
                    "duration": duration,
                    "model_used": video_model,
                    "task_id": video_result.get("task_id")
                }
            else:
                return {
                    "success": False,
                    "error": video_result.get("error")
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_multi_panel_anime(self,
                                    image_url: str,
                                    panels: List[Dict],
                                    prompts: List[str],
                                    transition_style: str = "smooth") -> Dict[str, Any]:
        """
        为多个分格生成连续的动画，并拼接成完整视频

        Args:
            image_url: 原始图片 URL
            panels: 分格列表
            prompts: 每个分格对应的动画提示词
            transition_style: 转场风格 ("smooth", "fade", "slide", "zoom")

        Returns:
            Dict: 生成的视频信息
        """
        # 1. 为每个分格生成动画
        panel_videos = []
        for i, (panel, prompt) in enumerate(zip(panels, prompts)):
            bbox = panel.get("bbox")
            if not bbox:
                continue

            result = self.generate_panel_animation(
                image_url=image_url,
                panel_bbox=bbox,
                prompt=prompt,
                duration=3,
                motion_strength=0.5
            )

            if result.get("success"):
                panel_videos.append({
                    "panel_index": i,
                    "video_url": result.get("video_url"),
                    "preview_url": result.get("preview_url")
                })

        if not panel_videos:
            return {
                "success": False,
                "error": "No panels were successfully generated"
            }

        # 2. 拼接视频并添加转场
        try:
            stitched_result = self._stitch_videos(panel_videos, transition_style)
            return {
                "success": True,
                "video_url": stitched_result.get("video_url"),
                "preview_url": stitched_result.get("preview_url"),
                "panel_count": len(panel_videos),
                "total_duration": stitched_result.get("duration"),
                "transition_style": transition_style
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== 多轮对话管理 ====================
    def manage_conversation_history(self,
                                     session_id: str,
                                     new_message: Dict,
                                     history: List[Dict],
                                     max_turns: int = 10,
                                     summary_threshold: int = 5) -> Tuple[List[Dict], Optional[str]]:
        """
        管理多轮对话历史，自动总结过期内容

        Args:
            session_id: 会话 ID
            new_message: 新消息
            history: 当前历史
            max_turns: 最大保留轮次
            summary_threshold: 触发总结的轮次阈值

        Returns:
            Tuple: (更新后的历史，总结内容（如果有）)
        """
        # 添加新消息
        updated_history = history + [new_message]

        # 如果超过阈值，进行总结
        if len(updated_history) >= summary_threshold * 2:
            summary = self._summarize_conversation(updated_history[:-summary_threshold])

            # 保留最近的轮次 + 总结
            condensed_history = [
                {"role": "system", "content": f"历史对话总结：{summary}"},
            ] + updated_history[-summary_threshold:]

            current_app.logger.info(f"Session {session_id}: Summarized {len(updated_history) - summary_threshold} turns")
            return condensed_history, summary

        return updated_history, None

    def _summarize_conversation(self, messages: List[Dict]) -> str:
        """总结对话历史"""
        try:
            # 构建总结请求
            conversation_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in messages
            ])

            prompt = f"""请总结以下对话的核心内容，提取关键信息和决策：

{conversation_text}

请用简洁的语言总结（100 字以内）："""

            # 调用语言模型进行总结
            result = qwen_ai_service.process_request({
                "task_type": "summarize",
                "content": {
                    "user_prompt": prompt
                },
                "parameters": {
                    "max_tokens": 200
                }
            })

            if result.get("success"):
                return result.get("result", "对话总结不可用")
            return "对话总结失败"

        except Exception as e:
            current_app.logger.error(f"Conversation summary failed: {e}")
            return "对话总结不可用"

    # ==================== 内部辅助方法 ====================
    def _call_vision_model(self,
                           model: str,
                           system_prompt: str,
                           image_url: str,
                           context: List[Dict] = None,
                           expect_json: bool = False) -> Any:
        """调用视觉模型"""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.extend(context)

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "请分析这张图片"},
                {"type": "image_url", "image_url": image_url}
            ]
        })

        payload = {
            "model": model,
            "messages": messages
        }

        if expect_json:
            payload["response_format"] = {"type": "json_object"}

        response = requests.post(
            f"{self._api_base}/services/aigc/text-generation/generation",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            raise Exception(f"Vision API error: {response.status_code} - {response.text}")

        result = response.json()
        content = result.get("output", {}).get("text", "")

        if expect_json:
            return json.loads(content)
        return content

    def _call_video_generation_api(self, payload: Dict) -> Dict:
        """调用视频生成 API"""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        # 提交任务
        submit_response = requests.post(
            f"{self._api_base}/services/aigc/video-generation/v1/tasks",
            headers=headers,
            json=payload,
            timeout=30
        )

        if submit_response.status_code != 200:
            return {
                "success": False,
                "error": f"Video generation API error: {submit_response.status_code}"
            }

        task_result = submit_response.json()
        task_id = task_result.get("task_id")

        # 轮询任务状态
        for _ in range(60):  # 最多等待 60 秒
            time.sleep(5)

            status_response = requests.get(
                f"{self._api_base}/services/aigc/video-generation/v1/tasks/{task_id}",
                headers=headers,
                timeout=30
            )

            if status_response.status_code == 200:
                status_result = status_response.json()
                status = status_result.get("status", "pending")

                if status == "succeeded":
                    return {
                        "success": True,
                        "video_url": status_result.get("output", {}).get("video_url"),
                        "preview_url": status_result.get("output", {}).get("preview_url"),
                        "task_id": task_id
                    }
                elif status == "failed":
                    return {
                        "success": False,
                        "error": status_result.get("message", "Video generation failed")
                    }

        return {
            "success": False,
            "error": "Video generation timeout"
        }

    def _crop_image_region(self, image_url: str, bbox: List[int]) -> str:
        """裁剪图片区域（返回临时 URL）"""
        # 这里可以使用阿里云 OSS 的图片处理功能
        # 格式：https://bucket.oss-cn-region.aliyuncs.com/image.jpg?x-oss-process=image/crop,x_100,y_100,w_200,h_150
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1

        # 如果是 OSS URL，添加裁剪参数
        if "aliyuncs.com" in image_url:
            separator = "&" if "?" in image_url else "?"
            crop_param = f"x-oss-process=image/crop,x_{x1},y_{y1},w_{width},h_{height}"
            return f"{image_url}{separator}{crop_param}"

        # 否则返回原 URL（实际部署时需要实现真正的裁剪逻辑）
        return image_url

    def _stitch_videos(self, videos: List[Dict], transition_style: str) -> Dict:
        """拼接多个视频片段"""
        # 这里需要调用视频拼接服务
        # 目前返回一个占位结果
        return {
            "video_url": videos[0].get("video_url"),  # 暂时返回第一个视频
            "preview_url": videos[0].get("preview_url"),
            "duration": len(videos) * 3  # 假设每个视频 3 秒
        }


# 全局实例
video_generation_service = VideoGenerationService()
