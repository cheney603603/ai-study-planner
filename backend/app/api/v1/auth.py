"""认证 API"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import (
    SendCodeRequest, SendCodeResponse,
    LoginRequest, LoginResponse, UserInfo
)
from app.services.auth_service import AuthService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("api.auth")


@router.post("/send-code", response_model=SendCodeResponse)
async def send_verification_code(
    request: SendCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    发送验证码
    
    - 验证码有效期 5 分钟
    - 同一手机号 60 秒内不能重复发送
    """
    logger.info(f"发送验证码请求: {request.phone}")
    
    service = AuthService(db)
    try:
        await service.send_verification_code(request.phone)
        return SendCodeResponse(
            code="success",
            message="验证码已发送",
            expire_seconds=300
        )
    except Exception as e:
        logger.error(f"发送验证码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败，请稍后重试"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    验证码登录
    
    - 验证通过后返回 JWT Token
    - Token 有效期 7 天
    """
    logger.info(f"登录请求: {request.phone}")
    
    service = AuthService(db)
    try:
        result = await service.login(request.phone, request.code)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="验证码错误或已过期"
            )
        
        return LoginResponse(
            code="success",
            access_token=result["access_token"],
            token_type="bearer",
            expires_in=result["expires_in"],
            user=result.get("user")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    current_user: dict = None  # 暂时简化，后续实现依赖注入
):
    """获取当前用户信息"""
    # TODO: 实现 JWT 验证依赖
    return UserInfo(
        id="test-user-id",
        phone="13800138000",
        nickname="测试用户",
        level="入门",
        total_score=0
    )
