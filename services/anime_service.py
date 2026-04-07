"""
Anime Generation Service 模块
提供漫画图片动画生成等业务逻辑服务
职责：纯粹的视频生成逻辑，不直接处理数据库存储等副作用
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AnimeGenerationService:
    """
    Anime Generation 服务类 - 纯粹的视频生成业务逻辑

    职责边界:
    - 负责调用 video_generation_service 进行视频生成
    - 不直接处理数据库存储、asset 关联等业务逻辑
    - 通过 db 层服务进行数据持久化
    """

    def __init__(self):
        self._video_generation_service = None
        self._conversation_history = None

    def initialize(self, video_generation_service, conversation_history):
        """初始化服务依赖"""
        self._video_generation_service = video_generation_service
        self._conversation_history = conversation_history

    @property
    def video_generation_service(self):
        if self._video_generation_service is None:
            from services import video_generation_service
            self._video_generation_service = video_generation_service
        return self._video_generation_service

    @property
    def conversation_history(self):
        if self._conversation_history is None:
            from services.conversation_history import conversation_history
            self._conversation_history = conversation_history
        return self._conversation_history

    def generate_anime(self, session_id: str, user_id: str,
                       first_frame_url: str, first_frame_oss_key: str,
                       last_frame_url: Optional[str], last_frame_oss_key: Optional[str],
                       parameters: Dict, work_id: str = None,
                       shot_id: str = None) -> Dict:
        """
        生成动画 - 主入口方法，根据帧模式分发到具体实现

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            first_frame_url: 首帧图片 URL
            first_frame_oss_key: 首帧 OSS 对象键
            last_frame_url: 尾帧图片 URL (单帧模式为 None)
            last_frame_oss_key: 尾帧 OSS 对象键 (单帧模式为 None)
            parameters: 生成参数
            work_id: 作品 ID (可选，用于关联作品)
            shot_id: 镜头 ID (可选，用于关联镜头)

        Returns:
            Dict: 包含成功状态和结果数据
        """
        # 获取模型配置
        model_config = self.video_generation_service.get_current_model_config()
        video_model = model_config["video_model"]

        # 组装公共生成参数
        user_prompt = parameters.get('prompt', '')
        style = parameters.get('style', 'anime')
        prompt = f"漫画图片，{style}风格，自然流畅的动画效果，{user_prompt}"

        # 根据是否提供尾帧 URL 判断帧模式，并组装完整的 payload
        if last_frame_url:
            # 首尾帧模式 payload
            payload = {
                "model": video_model,
                "input": {
                    "first_frame_url": first_frame_url,
                    "last_frame_url": last_frame_url,
                    "prompt": prompt
                },
                "parameters": {
                    "duration": parameters.get('duration', 5),
                    "resolution": "720P",
                    "motion_strength": parameters.get('motion_strength', 0.5)
                }
            }
            # 调用首尾帧模式
            return self._generate_start_end_frame_anime(
                session_id=session_id,
                payload=payload,
                api_endpoint='/services/aigc/image2video/video-synthesis',
                work_id=work_id,
                shot_id=shot_id
            )
        else:
            # 单帧模式 payload
            payload = {
                "model": video_model,
                "input": {
                    "img_url": first_frame_url,
                    "prompt": prompt
                },
                "parameters": {
                    "duration": parameters.get('duration', 5),
                    "resolution": "720P",
                    "motion_strength": parameters.get('motion_strength', 0.5)
                }
            }
            # 调用单帧模式
            return self._generate_single_frame_anime(
                session_id=session_id,
                payload=payload,
                api_endpoint='/services/aigc/video-generation/video-synthesis',
                work_id=work_id,
                shot_id=shot_id
            )

    def _generate_single_frame_anime(self, session_id: str,
                                      payload: Dict,
                                      api_endpoint: str,
                                      work_id: str = None,
                                      shot_id: str = None) -> Dict:
        """
        为单张图片生成动画（首帧模式）

        Args:
            session_id: 会话 ID
            payload: 完整的 API payload
            api_endpoint: API 端点路径
            work_id: 作品 ID (可选，原样返回)
            shot_id: 镜头 ID (可选，原样返回)

        Returns:
            Dict: 包含成功状态和视频信息
        """
        result = self.video_generation_service.call_video_api(
            payload=payload,
            api_endpoint=api_endpoint,
            session_id=session_id,
            conversation_history=self.conversation_history
        )

        if result.get('success'):
            return {
                'success': True,
                'session_id': session_id,
                'video_url': result.get('video_url'),
                'panel_count': 1,
                'total_duration': result.get('duration', payload['parameters'].get('duration', 5)),
                'frame_mode': 'single',
                'task_id': result.get('task_id'),
                'work_id': work_id,
                'shot_id': shot_id
            }
        return {
            'success': False,
            'error': f"Animation generation failed: {result.get('error')}"
        }

    def _generate_start_end_frame_anime(self, session_id: str,
                                         payload: Dict,
                                         api_endpoint: str,
                                         work_id: str = None,
                                         shot_id: str = None) -> Dict:
        """
        为两张图片生成动画（首尾帧模式）

        Args:
            session_id: 会话 ID
            payload: 完整的 API payload
            api_endpoint: API 端点路径
            work_id: 作品 ID (可选，原样返回)
            shot_id: 镜头 ID (可选，原样返回)

        Returns:
            Dict: 包含成功状态和视频信息
        """
        result = self.video_generation_service.call_video_api(
            payload=payload,
            api_endpoint=api_endpoint,
            session_id=session_id,
            conversation_history=self.conversation_history
        )

        if result.get('success'):
            return {
                'success': True,
                'session_id': session_id,
                'video_url': result.get('video_url'),
                'panel_count': 1,
                'total_duration': result.get('duration', payload['parameters'].get('duration', 5)),
                'frame_mode': 'start_end',
                'task_id': result.get('task_id'),
                'work_id': work_id,
                'shot_id': shot_id
            }
        return {
            'success': False,
            'error': f"Animation generation failed: {result.get('error')}"
        }

    def generate_multi_image_anime(self, session_id: str, user_id: str,
                                    images: List[Dict], parameters: Dict,
                                    work_id: str = None,
                                    shot_id: str = None) -> Dict:
        """
        为多张图片依次生成动画，最后合并成一个视频

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            images: 图片列表，每个元素包含 {'picture_url': str, 'oss_object_key': str}
            parameters: 生成参数
            work_id: 作品 ID (可选，原样返回)
            shot_id: 镜头 ID (可选，原样返回)

        Returns:
            Dict: 包含成功状态和结果数据
        """
        if not images or len(images) == 0:
            return {'success': False, 'error': 'At least one image is required'}

        model_config = self.video_generation_service.get_current_model_config()
        video_model = model_config["video_model"]

        user_prompt = parameters.get('prompt', '')
        style = parameters.get('style', 'anime')
        prompt = f"漫画图片，{style}风格，自然流畅的动画效果，{user_prompt}"
        frame_mode = parameters.get('frame_mode', 'single')

        video_results = []
        total_duration = 0

        for i, image in enumerate(images):
            picture_url = image.get('picture_url')
            oss_object_key = image.get('oss_object_key')

            logger.info(f"Generating animation for image {i+1}/{len(images)}: {oss_object_key}")

            if frame_mode == 'start_end' and i < len(images) - 1:
                next_image = images[i + 1]
                end_image_url = next_image.get('picture_url')
                logger.info(f"Using start_end frame mode: {picture_url} -> {end_image_url}")

                payload = {
                    "model": video_model,
                    "input": {
                        "first_frame_url": picture_url,
                        "last_frame_url": end_image_url,
                        "prompt": prompt
                    },
                    "parameters": {
                        "duration": parameters.get('duration', 5),
                        "resolution": "720P",
                        "motion_strength": parameters.get('motion_strength', 0.5)
                    }
                }
                api_endpoint = '/services/aigc/image2video/video-synthesis'
            else:
                payload = {
                    "model": video_model,
                    "input": {
                        "img_url": picture_url,
                        "prompt": prompt
                    },
                    "parameters": {
                        "duration": parameters.get('duration', 5),
                        "resolution": "720P",
                        "motion_strength": parameters.get('motion_strength', 0.5)
                    }
                }
                api_endpoint = '/services/aigc/video-generation/video-synthesis'

            result = self.video_generation_service.call_video_api(
                payload=payload,
                api_endpoint=api_endpoint,
                session_id=session_id,
                conversation_history=self.conversation_history
            )

            if result.get('success'):
                video_results.append(result)
                total_duration += result.get('duration', parameters.get('duration', 5))
            else:
                logger.error(f"Failed to generate animation for image {i+1}: {result.get('error')}")
                return {
                    'success': False,
                    'error': f"Failed to generate animation for image {i+1}: {result.get('error')}",
                    'processed_count': i,
                    'total_count': len(images)
                }

        logger.info(f"All {len(images)} animations generated, merging videos...")

        merge_result = self.video_generation_service.merge_videos(
            video_urls=[r.get('video_url') for r in video_results],
            transition_type=parameters.get('transition', 'fade'),
            transition_duration=parameters.get('transition_duration', 0.5)
        )

        if merge_result.get('success'):
            self.conversation_history.add_message(
                session_id=session_id,
                role='assistant',
                content=f"已为 {len(images)} 张图片生成动画并合并（帧模式：{frame_mode}）",
                metadata={
                    'merged_video_url': merge_result.get('video_url'),
                    'panel_count': len(images),
                    'total_duration': total_duration,
                    'frame_mode': frame_mode
                }
            )

            return {
                'success': True,
                'session_id': session_id,
                'video_url': merge_result.get('video_url'),
                'panel_count': len(images),
                'total_duration': total_duration,
                'individual_videos': video_results,
                'frame_mode': frame_mode,
                'work_id': work_id,
                'shot_id': shot_id
            }
        return {
            'success': False,
            'error': f"Failed to merge videos: {merge_result.get('error')}"
        }

    def chat(self, session_id: str, user_id: str, picture_url: str, oss_object_key: str,
             user_message: str) -> Dict:
        """
        处理对话模式：多轮对话交互

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            picture_url: 图片 URL
            oss_object_key: OSS 对象键
            user_message: 用户消息

        Returns:
            Dict: 包含成功状态和结果数据
        """
        if not user_message:
            return {
                'success': False,
                'error': 'Message is required for chat mode'
            }

        # 获取或创建会话
        session = self.conversation_history.get_session(session_id)
        if not session:
            self.conversation_history.create_session(
                session_id=session_id,
                user_id=user_id,
                context_type='anime_generation',
                context_data={
                    'asset_id': None,
                    'oss_object_key': oss_object_key,
                    'image_url': picture_url
                }
            )

        # 获取更新后的历史（包含自动总结）
        updated_messages = self.conversation_history.get_messages(session_id, include_summaries=True)

        # 构建发送给 AI 的完整 prompt
        system_prompt = """你是一位专业的漫画动画生成助手。你可以帮助用户：
1. 分析漫画图片内容和分格
2. 为静态漫画分格生成动态动画
3. 调整动画的风格、转场效果等参数
4. 提供创作建议和技术支持

请用友好、专业的语气回答用户的问题。如果涉及技术参数，请提供清晰的说明。"""

        # 存储发送给 AI 的完整请求（user 角色）- 记录与大模型交互的输入
        ai_request_payload = {
            "system_prompt": system_prompt,
            "user_prompt": user_message,
            "context": updated_messages[-10:] if len(updated_messages) > 10 else updated_messages,
            "image_url": picture_url
        }
        self.conversation_history.add_message(
            session_id=session_id,
            role='user',
            content=user_message,
            metadata={'ai_request_payload': ai_request_payload, 'image_url': picture_url}
        )

        # 使用 AI 生成回复
        ai_response = self._generate_chat_response(user_message, updated_messages, picture_url)

        # 添加 AI 回复到历史，同时存储完整的 AI 响应 payload - 记录与大模型交互的输出
        ai_response_payload = {
            "response": ai_response,
            "model": "qwen3.5-plus",
            "request_prompt": user_message
        }
        self.conversation_history.add_message(
            session_id=session_id,
            role='assistant',
            content=ai_response,
            metadata={'ai_response_payload': ai_response_payload}
        )

        # 重新获取历史以获取总结
        _, summary = self.conversation_history.get_messages(session_id, include_summaries=True)

        return {
            'success': True,
            'session_id': session_id,
            'response': ai_response,
            'summary': summary,
            'turn_count': len(updated_messages)
        }

    def confirm(self, user_id: str, work_id: str, parameters: Dict,
                shot_id: str = None) -> Dict:
        """
        处理确认模式：用户确认保存生成的视频

        Args:
            user_id: 用户 ID
            work_id: 作品 ID
            shot_id: 镜头 ID (可选)
            parameters: 包含视频 URL 等参数

        Returns:
            Dict: 包含成功状态和结果数据
        """
        from db import MySQLService, MongoService, oss_service

        video_url = parameters.get('video_url')
        if not video_url:
            return {'success': False, 'error': 'video_url is required for confirm mode'}

        mysql_row = MySQLService().insert_asset(user_id, 'comic_video', work_id)
        asset_id = mysql_row['asset_id']
        oss_object_key = oss_service.generate_video_object_key(user_id, asset_id)
        oss_result = oss_service.save_video_from_url(video_url, oss_object_key)

        if not oss_result.get('success'):
            MySQLService().delete_asset(asset_id)
            return {'success': False, 'error': oss_result.get('error')}

        video_asset_data = {
            'type': 'comic_video',
            'video_url': oss_result.get('oss_url'),
            'source_asset_id': None,
            'oss_object_key': oss_result.get('oss_object_key'),
            'work_id': work_id,
            'shot_id': shot_id,
            'parameters': parameters,
            'created_at': datetime.now().isoformat()
        }

        try:
            MongoService().insert_asset_data(asset_id, video_asset_data)
        except Exception as e:
            logger.error(f"Error saving video asset data: {e}")
            oss_service.delete_video(oss_result.get('oss_object_key'))
            MySQLService().delete_asset(asset_id)
            return {'success': False, 'error': 'Failed to save video'}

        if self.conversation_history:
            self.conversation_history.add_message(
                session_id=parameters.get('session_id', 'default'),
                role='assistant',
                content='视频已保存到 OSS',
                metadata={
                    'asset_id': asset_id,
                    'oss_object_key': oss_result.get('oss_object_key'),
                    'work_id': work_id,
                    'shot_id': shot_id
                }
            )

        return {
            'success': True,
            'asset_id': asset_id,
            'video_url': oss_result.get('oss_url'),
            'oss_object_key': oss_result.get('oss_object_key'),
            'work_id': work_id,
            'shot_id': shot_id
        }

    def _generate_chat_response(self, user_message: str, messages: List[Dict], image_url: str) -> str:
        """
        使用 AI 生成聊天回复

        Args:
            user_message: 用户消息
            messages: 对话历史
            image_url: 关联的图片 URL

        Returns:
            str: AI 生成的回复
        """
        from services.ai_service import qwen_ai_service

        # 构建系统提示
        system_prompt = """你是一位专业的漫画动画生成助手。你可以帮助用户：
1. 分析漫画图片内容和分格
2. 为静态漫画分格生成动态动画
3. 调整动画的风格、转场效果等参数
4. 提供创作建议和技术支持

请用友好、专业的语气回答用户的问题。如果涉及技术参数，请提供清晰的说明。"""

        # 构建消息
        content = []
        if image_url:
            content.append({"type": "text", "text": f"参考图片：{image_url}\n"})
        content.append({"type": "text", "text": user_message})

        try:
            result = qwen_ai_service.process_request({
                "task_type": "chat",
                "content": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_message,
                    "context": messages[-10:] if len(messages) > 10 else messages  # 限制上下文长度
                },
                "parameters": {
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            })

            if result.get('success'):
                return result.get('result', '抱歉，我暂时无法生成回复。')
            return f"抱歉，生成回复时出错：{result.get('error', '未知错误')}"

        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return '抱歉，我暂时无法生成回复，请稍后重试。'


# 全局实例
anime_generation_service = AnimeGenerationService()
