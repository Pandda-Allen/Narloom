"""
对话历史管理服务
使用 MongoDB 存储会话历史，支持多轮对话和自动总结
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from services.mongo_service import MongoService
from services.mysql_service import MySQLService
import logging

logger = logging.getLogger(__name__)


class ConversationHistory:
    """对话历史管理类"""

    # MongoDB collection 名称
    COLLECTION_NAME = "conversation_history"

    # 默认配置
    DEFAULT_MAX_TURNS = 10  # 最大保留轮次
    DEFAULT_SUMMARY_THRESHOLD = 5  # 触发总结的轮次阈值
    DEFAULT_EXPIRY_HOURS = 24  # 会话过期时间（小时）

    def __init__(self):
        self.mongo_service = MongoService()
        self.mysql_service = MySQLService()

    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        try:
            collection = self._get_collection()
            session = collection.find_one({"session_id": session_id})
            return session
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None

    def create_session(self,
                       session_id: str,
                       user_id: str,
                       context_type: str = "anime_generation",
                       context_data: Dict = None) -> Dict:
        """
        创建新会话

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            context_type: 上下文类型（如：anime_generation, comic_analysis 等）
            context_data: 上下文相关数据（如图片 URL、asset_id 等）
        """
        try:
            collection = self._get_collection()

            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "context_type": context_type,
                "context_data": context_data or {},
                "messages": [],
                "summaries": [],
                "turn_count": 0,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=self.DEFAULT_EXPIRY_HOURS)
            }

            collection.insert_one(session_data)
            logger.info(f"Created session {session_id} for user {user_id}")
            return session_data

        except Exception as e:
            logger.error(f"Error creating session {session_id}: {e}")
            raise

    def add_message(self,
                    session_id: str,
                    role: str,
                    content: str,
                    metadata: Dict = None) -> Tuple[List[Dict], Optional[str]]:
        """
        添加消息到会话，并管理历史

        Args:
            session_id: 会话 ID
            role: 角色（user/assistant/system）
            content: 消息内容
            metadata: 额外元数据

        Returns:
            Tuple: (更新后的消息历史，总结内容（如果有）)
        """
        try:
            collection = self._get_collection()

            session = self.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # 添加新消息
            message = {
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.now()
            }

            session["messages"].append(message)
            session["turn_count"] += 1
            session["updated_at"] = datetime.now()

            summary = None

            # 检查是否需要进行历史总结
            if session["turn_count"] >= self.DEFAULT_SUMMARY_THRESHOLD * 2:
                # 提取需要总结的消息
                messages_to_summarize = session["messages"][:-self.DEFAULT_SUMMARY_THRESHOLD]

                # 调用总结服务
                summary = self._summarize_messages(messages_to_summarize)

                if summary:
                    # 保存总结
                    session["summaries"].append({
                        "content": summary,
                        "created_at": datetime.now(),
                        "message_count": len(messages_to_summarize)
                    })

                    # 移除已总结的消息，保留最近的
                    session["messages"] = session["messages"][-self.DEFAULT_SUMMARY_THRESHOLD:]
                    session["turn_count"] = len(session["messages"])

                    logger.info(f"Session {session_id}: Summarized {len(messages_to_summarize)} messages")

            # 更新会话
            collection.update_one(
                {"session_id": session_id},
                {"$set": session}
            )

            return session["messages"], summary

        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {e}")
            raise

    def get_messages(self,
                     session_id: str,
                     include_summaries: bool = True,
                     max_messages: int = None) -> List[Dict]:
        """
        获取会话消息

        Args:
            session_id: 会话 ID
            include_summaries: 是否包含历史总结
            max_messages: 最大返回消息数
        """
        session = self.get_session(session_id)
        if not session:
            return []

        messages = session.get("messages", [])

        # 如果有总结且需要包含，将最新总结作为系统消息添加
        if include_summaries and session.get("summaries"):
            latest_summary = session["summaries"][-1]["content"]
            system_message = {
                "role": "system",
                "content": f"历史对话摘要：{latest_summary}"
            }
            messages = [system_message] + messages

        # 限制返回数量
        if max_messages and len(messages) > max_messages:
            messages = messages[-max_messages:]

        return messages

    def update_context_data(self, session_id: str, data: Dict):
        """更新会话上下文数据"""
        try:
            collection = self._get_collection()
            collection.update_one(
                {"session_id": session_id},
                {"$set": {"context_data": data, "updated_at": datetime.now()}}
            )
        except Exception as e:
            logger.error(f"Error updating context data for session {session_id}: {e}")

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            collection = self._get_collection()
            result = collection.delete_one({"session_id": session_id})
            logger.info(f"Deleted session {session_id}")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        try:
            collection = self._get_collection()
            result = collection.delete_many({
                "expires_at": {"$lt": datetime.now()}
            })
            logger.info(f"Cleaned up {result.deleted_count} expired sessions")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0

    def _get_collection(self):
        """获取 MongoDB collection"""
        # 确保 MongoDB 已初始化
        if not self.mongo_service._initialized:
            raise RuntimeError("MongoDB service not initialized")

        return self.mongo_service._work_details_collection.database[self.COLLECTION_NAME]

    def _summarize_messages(self, messages: List[Dict]) -> Optional[str]:
        """
        总结消息列表

        使用 Qwen AI 进行总结
        """
        try:
            from services.ai_service import qwen_ai_service

            # 构建总结文本
            conversation_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')[:500]}"  # 限制每条消息长度
                for msg in messages
            ])

            prompt = f"""请总结以下对话的核心内容，提取关键信息和决策点：

{conversation_text}

总结要求：
1. 保留关键的技术参数和配置
2. 记录用户的主要需求和偏好
3. 总结已达成的共识和待确认的事项
4. 控制在 200 字以内

总结："""

            result = qwen_ai_service.process_request({
                "task_type": "summarize",
                "content": {
                    "user_prompt": prompt
                },
                "parameters": {
                    "max_tokens": 300,
                    "temperature": 0.3
                }
            })

            if result.get("success"):
                return result.get("result")
            return None

        except Exception as e:
            logger.error(f"Error summarizing messages: {e}")
            return None


# 全局实例
conversation_history = ConversationHistory()
