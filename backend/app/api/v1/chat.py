"""聊天 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import (
    SendMessageRequest, SendMessageResponse,
    ChatMessage, SessionResponse
)
from app.services.chat_service import ChatService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("api.chat")


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = "test-user-id"  # TODO: 替换为真实用户认证
):
    """
    发送消息给 AI 智能体
    
    - 支持多轮对话
    - 自动路由到对应的 Agent
    - 记录 Token 消耗
    """
    logger.info(f"用户 {user_id} 发送消息: {request.content[:50]}...")
    
    service = ChatService(db)
    try:
        result = await service.process_message(
            user_id=user_id,
            content=request.content,
            session_id=request.session_id,
            session_type=request.session_type
        )
        
        return SendMessageResponse(
            code="success",
            session_id=result["session_id"],
            message=result["message"],
            token_used=result["token_used"]
        )
    except Exception as e:
        logger.error(f"处理消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")


@router.get("/sessions")
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    user_id: str = "test-user-id"
):
    """获取用户的会话列表"""
    service = ChatService(db)
    sessions = await service.get_user_sessions(user_id)
    return {"sessions": sessions}


@router.get("/history/{session_id}")
async def get_session_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取会话历史"""
    service = ChatService(db)
    messages = await service.get_session_messages(session_id)
    return {
        "session_id": session_id,
        "messages": messages
    }
