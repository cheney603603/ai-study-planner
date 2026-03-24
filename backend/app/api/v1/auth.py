"""认证 API"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.schemas.auth import (
    SendCodeRequest, SendCodeResponse,
    LoginRequest, LoginResponse, UserInfo
)
from app.schemas.common import DataResponse
from app.services.auth_service import AuthService
from app.dependencies import get_current_user, get_current_user_id
from app.models.user import User
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("api.auth")


@router.post("/send-code", response_model=DataResponse)
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
        success = await service.send_verification_code(request.phone)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="发送过于频繁，请稍后再试"
            )
        
        return DataResponse(
            code="success",
            message="验证码已发送",
            data={"expire_seconds": 300}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送验证码失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败，请稍后重试"
        )


@router.post("/login", response_model=DataResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    验证码登录
    
    - 验证通过后返回 JWT Token
    - Token 有效期 7 天
    - 开发环境：任意 6 位数字验证码
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
        
        return DataResponse(
            code="success",
            message="登录成功",
            data={
                "access_token": result["access_token"],
                "token_type": "bearer",
                "expires_in": result["expires_in"],
                "user": result.get("user")
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.get("/me", response_model=DataResponse)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前登录用户信息"""
    return DataResponse(
        code="success",
        data=UserInfo(
            id=current_user.id,
            phone=current_user.phone,
            nickname=current_user.nickname,
            avatar_url=current_user.avatar_url,
            level=current_user.level,
            total_score=current_user.total_score
        )
    )


@router.put("/profile", response_model=DataResponse)
async def update_profile(
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户资料"""
    service = AuthService(db)
    
    user = await service.update_user_profile(
        user_id=current_user.id,
        nickname=nickname,
        avatar_url=avatar_url
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return DataResponse(
        code="success",
        message="资料更新成功",
        data=UserInfo(
            id=user.id,
            phone=user.phone,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            level=user.level,
            total_score=user.total_score
        )
    )
