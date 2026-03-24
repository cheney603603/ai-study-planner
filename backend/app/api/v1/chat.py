"""聊天 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import (
    SendMessageRequest, SendMessageResponse,
    ChatMessage, SessionResponse
)
from app.schemas.common import DataResponse
from app.services.chat_service import ChatService
from app.services.token_manager import TokenManager
from app.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.core.exceptions import TokenQuotaExceededError

router = APIRouter()
logger = get_logger("api.chat")


@router.post("/send", response_model=DataResponse)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    发送消息给 AI 智能体
    
    - 支持多轮对话
    - 自动路由到对应的 Agent
    - 自动记录 Token 消耗
    """
    logger.info(f"用户 {user_id} 发送消息: {request.content[:50]}...")
    
    # 检查 Token 配额（估算消耗）
    token_manager = TokenManager(db)
    if not await token_manager.check_quota(user_id, required_tokens=100):
        raise HTTPException(
            status_code=429,
            detail="Token 配额不足，请升级会员"
        )
    
    service = ChatService(db)
    
    try:
        result = await service.process_message(
            user_id=user_id,
            content=request.content,
            session_id=request.session_id,
            session_type=request.session_type
        )
        
        # 消耗 Token
        token_used = result.get("token_used", 0)
        if token_used > 0:
            try:
                await token_manager.consume_tokens(user_id, token_used)
            except TokenQuotaExceededError:
                logger.warning(f"Token 配额不足: user={user_id}")
        
        return DataResponse(
            code="success",
            data={
                "session_id": result["session_id"],
                "message": {
                    "role": "assistant",
                    "content": result["message"].content,
                    "timestamp": result["message"].timestamp.isoformat() if hasattr(result["message"], 'timestamp') else None
                },
                "token_used": token_used
            }
        )
    except TokenQuotaExceededError:
        raise HTTPException(
            status_code=429,
            detail="Token 配额不足"
        )
    except Exception as e:
        logger.error(f"处理消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")


@router.get("/sessions", response_model=DataResponse)
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取用户的会话列表"""
    service = ChatService(db)
    sessions = await service.get_user_sessions(user_id)
    return DataResponse(
        code="success",
        data={"sessions": sessions}
    )


@router.get("/history/{session_id}", response_model=DataResponse)
async def get_session_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取会话历史"""
    service = ChatService(db)
    messages = await service.get_session_messages(session_id)
    return DataResponse(
        code="success",
        data={
            "session_id": session_id,
            "messages": messages
        }
    )


@router.post("/sessions/new", response_model=DataResponse)
async def create_new_session(
    session_type: str = "goal_discussion",
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """创建新会话"""
    service = ChatService(db)
    
    # 创建会话
    from app.models.badge import ChatSession
    import uuid
    
    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        session_type=session_type,
        status="active",
        messages=[]
    )
    db.add(session)
    await db.commit()
    
    return DataResponse(
        code="success",
        message="会话创建成功",
        data={
            "session_id": session.id,
            "session_type": session_type
        }
    )
