"""聊天服务"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.badge import ChatSession
from app.schemas.chat import ChatMessage
from app.core.logging import get_logger
from app.agents.agent_router import AgentRouter

logger = get_logger("service.chat")


class ChatService:
    """聊天服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_router = AgentRouter()

    async def process_message(
        self,
        user_id: str,
        content: str,
        session_id: Optional[str] = None,
        session_type: str = "goal_discussion",
    ) -> dict:
        """
        处理用户消息

        1. 获取或创建会话
        2. 从会话恢复 collected_info 上下文
        3. 调用 Agent 处理
        4. 持久化消息历史和 collected_info
        5. 返回响应
        """
        session = await self._get_or_create_session(
            user_id=user_id,
            session_id=session_id,
            session_type=session_type,
        )

        # 从会话中恢复 collected_info（多轮对话持久化）
        session_context = {
            "collected_info": session.context or {},
        }

        # 调用 Agent
        agent_response = await self.agent_router.route(
            user_id=user_id,
            message=content,
            session_id=session.id,
            session_type=session_type,
            context=session_context,
            history=session.messages or [],
        )

        # 构建消息记录
        user_msg = ChatMessage(
            role="user",
            content=content,
            timestamp=datetime.utcnow(),
        )
        ai_msg = ChatMessage(
            role="assistant",
            content=agent_response["response"],
            timestamp=datetime.utcnow(),
        )

        # 更新消息历史（最多保留最近 100 条，防止单条记录无限膨胀）
        MAX_HISTORY = 100
        messages = list(session.messages or [])
        messages.append(user_msg.model_dump(mode="json", exclude_none=True))
        messages.append(ai_msg.model_dump(mode="json", exclude_none=True))
        if len(messages) > MAX_HISTORY:
            messages = messages[-MAX_HISTORY:]

        # 持久化 collected_info（从 Agent 返回的 metadata 中提取）
        new_collected_info = (
            agent_response.get("metadata", {}).get("collected_info")
            or session_context.get("collected_info")
            or {}
        )

        stmt = (
            update(ChatSession)
            .where(ChatSession.id == session.id)
            .values(
                messages=messages,
                context=new_collected_info,
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

        logger.info(
            f"消息处理完成: session={session.id}, "
            f"token_used={agent_response.get('token_used', 0)}"
        )

        return {
            "session_id": session.id,
            "message": ai_msg,
            "token_used": agent_response.get("token_used", 0),
            "metadata": agent_response.get("metadata", {}),
        }

    async def _get_or_create_session(
        self,
        user_id: str,
        session_id: Optional[str],
        session_type: str,
    ) -> ChatSession:
        """获取或创建会话"""
        if session_id:
            stmt = select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            if session:
                return session

        session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_type=session_type,
            status="active",
            messages=[],
            context={},
        )
        self.db.add(session)
        await self.db.commit()
        logger.info(f"创建新会话: {session.id}, type={session_type}")
        return session

    async def get_user_sessions(self, user_id: str) -> List[dict]:
        """获取用户的所有会话"""
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        return [
            {
                "id": s.id,
                "session_type": s.session_type,
                "status": s.status,
                "message_count": len(s.messages or []),
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions
        ]

    async def get_session_messages(self, session_id: str) -> List[dict]:
        """获取会话消息历史"""
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        return session.messages if session else []
