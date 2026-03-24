"""
Anime Service 模块
提供漫画图片动画生成等功能
"""
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class AnimeService:
    """Anime 服务类，提供漫画动画生成相关功能"""

    def __init__(self):
        pass

    def generate_anime(self, session_id: str, user_id: str, picture_url: str, oss_object_key: str,
                       parameters: Dict, conversation_history, video_generation_service) -> Dict:
        """
        为单张图片生成动画

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            picture_url: 图片 URL
            oss_object_key: OSS 对象键
            parameters: 生成参数
            conversation_history: 对话历史服务
            video_generation_service: 视频生成服务

        Returns:
            Dict: 包含成功状态和结果数据
        """
        # 为整张图片生成提示词
        user_prompt = parameters.get('prompt', '')
        style = parameters.get('style', 'anime')
        prompt = f"漫画图片，{style}风格，自然流畅的动画效果，{user_prompt}"

        # 直接为单张图片生成动画
        result = video_generation_service.generate_single_image_anime(
            image_url=picture_url,
            prompt=prompt,
            duration=parameters.get('duration', 5),
            motion_strength=parameters.get('motion_strength', 0.5)
        )

        if result.get('success'):
            conversation_history.add_message(
                session_id=session_id,
                role='assistant',
                content=f"动画生成完成",
                metadata={'video_result': result}
            )

            return {
                'success': True,
                'session_id': session_id,
                'video_url': result.get('video_url'),
                'preview_url': result.get('preview_url'),
                'panel_count': 1,
                'total_duration': result.get('duration', 5),
            }
        else:
            return {
                'success': False,
                'error': f"Animation generation failed: {result.get('error')}"
            }

    def chat(self, session_id: str, user_id: str, picture_url: str, oss_object_key: str,
             user_message: str, conversation_history) -> Dict:
        """
        处理对话模式：多轮对话交互

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            picture_url: 图片 URL
            oss_object_key: OSS 对象键
            user_message: 用户消息
            conversation_history: 对话历史服务

        Returns:
            Dict: 包含成功状态和结果数据
        """
        if not user_message:
            return {
                'success': False,
                'error': 'Message is required for chat mode'
            }

        # 获取或创建会话
        session = conversation_history.get_session(session_id)
        if not session:
            conversation_history.create_session(
                session_id=session_id,
                user_id=user_id,
                context_type='anime_generation',
                context_data={
                    'asset_id': None,
                    'oss_object_key': oss_object_key,
                    'image_url': picture_url
                }
            )

        # 添加用户消息
        conversation_history.add_message(
            session_id=session_id,
            role='user',
            content=user_message,
            metadata={'image_url': picture_url}
        )

        # 获取更新后的历史（包含自动总结）
        updated_messages = conversation_history.get_messages(session_id, include_summaries=True)

        # 使用 AI 生成回复
        ai_response = self._generate_chat_response(user_message, updated_messages, picture_url)

        # 添加 AI 回复到历史
        conversation_history.add_message(
            session_id=session_id,
            role='assistant',
            content=ai_response,
            metadata={}
        )

        # 重新获取历史以获取总结
        _, summary = conversation_history.get_messages(session_id, include_summaries=True)

        return {
            'success': True,
            'session_id': session_id,
            'response': ai_response,
            'summary': summary,
            'turn_count': len(updated_messages)
        }

    def confirm(self, user_id: str, parameters: Dict, conversation_history) -> Dict:
        """
        处理确认模式：用户确认保存生成的视频

        Args:
            user_id: 用户 ID
            parameters: 包含视频 URL 等参数
            conversation_history: 对话历史服务

        Returns:
            Dict: 包含成功状态和结果数据
        """
        from services.mysql_service import MySQLService
        from services.mongo_service import MongoService

        video_url = parameters.get('video_url')
        preview_url = parameters.get('preview_url')

        if not video_url:
            return {
                'success': False,
                'error': 'video_url is required for confirm mode'
            }

        # 创建资产记录保存视频
        mysql_row = MySQLService().insert_asset(user_id, 'comic_video', None)
        asset_id = mysql_row['asset_id']

        # 保存视频信息到 MongoDB
        video_asset_data = {
            'type': 'comic_video',
            'video_url': video_url,
            'preview_url': preview_url,
            'source_asset_id': None,
            'parameters': parameters,
            'created_at': datetime.now().isoformat()
        }

        try:
            MongoService().insert_asset_data(asset_id, video_asset_data)
        except Exception as e:
            logger.error(f"Error saving video asset data: {e}")
            MySQLService().delete_asset(asset_id)
            return {
                'success': False,
                'error': 'Failed to save video'
            }

        # 更新会话历史（记录保存操作）
        if conversation_history:
            pass  # 预留扩展位置

        return {
            'success': True,
            'asset_id': asset_id,
            'video_url': video_url,
            'preview_url': preview_url
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
anime_service = AnimeService()
