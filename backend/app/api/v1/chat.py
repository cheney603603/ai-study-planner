"""聊天 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import SendMessageRequest
from app.schemas.common import DataResponse
from app.services.chat_service import ChatService
from app.services.plan_service import PlanService
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
    user_id: str = Depends(get_current_user_id),
):
    """
    发送消息给 AI 智能体

    流程：先检查配额 → 调用 AI → 按实际消耗扣减（原子性保证）
    """
    logger.info(f"用户 {user_id} 发送消息: {request.content[:50]}...")

    token_manager = TokenManager(db)

    # 预检配额（估算 100 token）
    if not await token_manager.check_quota(user_id, required_tokens=100):
        raise HTTPException(status_code=429, detail="Token 配额不足，请升级会员")

    chat_service = ChatService(db)

    try:
        result = await chat_service.process_message(
            user_id=user_id,
            content=request.content,
            session_id=request.session_id,
            session_type=request.session_type,
        )

        # 按实际消耗扣减（AI 调用已完成，此处只记账）
        token_used = result.get("token_used", 0)
        if token_used > 0:
            try:
                await token_manager.consume_tokens(user_id, token_used)
            except TokenQuotaExceededError:
                # 配额在 AI 调用期间耗尽：记录警告但不回滚响应
                logger.warning(f"Token 配额在调用期间耗尽: user={user_id}, used={token_used}")

        metadata = result.get("metadata", {})
        response_data = {
            "session_id": result["session_id"],
            "message": {
                "role": "assistant",
                "content": result["message"].content,
            },
            "token_used": token_used,
        }

        if metadata.get("ready_to_save"):
            response_data["plan_ready"] = True
            response_data["plan_data"] = metadata.get("plan")

        return DataResponse(code="success", data=response_data)

    except TokenQuotaExceededError:
        raise HTTPException(status_code=429, detail="Token 配额不足")
    except Exception as e:
        logger.error(f"处理消息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理消息失败: {str(e)}")


@router.post("/confirm-plan", response_model=DataResponse)
async def confirm_and_create_plan(
    plan_data: dict,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """确认并创建学习计划"""
    logger.info(f"用户 {user_id} 确认创建学习计划")
    plan_service = PlanService(db)
    try:
        plan = await plan_service.create_plan_from_ai(user_id, plan_data)
        return DataResponse(
            code="success",
            message="学习计划创建成功！",
            data={
                "plan_id": plan.id,
                "title": plan.title,
                "start_date": plan.start_date.isoformat() if plan.start_date else None,
            },
        )
    except Exception as e:
        logger.error(f"创建计划失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=DataResponse)
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """获取用户的会话列表"""
    service = ChatService(db)
    sessions = await service.get_user_sessions(user_id)
    return DataResponse(code="success", data={"sessions": sessions})


@router.get("/history/{session_id}", response_model=DataResponse)
async def get_session_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取会话历史"""
    service = ChatService(db)
    messages = await service.get_session_messages(session_id)
    return DataResponse(
        code="success",
        data={"session_id": session_id, "messages": messages},
    )


@router.post("/sessions/new", response_model=DataResponse)
async def create_new_session(
    session_type: str = "goal_discussion",
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """创建新会话"""
    import uuid
    from app.models.badge import ChatSession

    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        session_type=session_type,
        status="active",
        messages=[],
        context={},
    )
    db.add(session)
    await db.commit()
    return DataResponse(
        code="success",
        message="会话创建成功",
        data={"session_id": session.id, "session_type": session_type},
    )
