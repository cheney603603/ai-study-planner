"""依赖注入"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_token
from app.services.auth_service import AuthService
from app.services.token_manager import TokenManager
from app.config import settings
from sqlalchemy import select

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    获取当前用户 ID（从 Token 中）

    - 生产环境：无 Token 直接 401
    - DEBUG 环境：无 Token 返回 test-user-id（方便本地调试）
    """
    if not credentials:
        if settings.DEBUG:
            return "test-user-id"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token 载荷",
        )

    return user_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前认证用户
    
    从 JWT Token 中提取用户 ID，查询数据库返回用户对象
    必须提供有效的 Token
    """
    token = credentials.credentials
    
    # 验证 Token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的 Token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 获取用户
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token 载荷"
        )
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return user


async def check_token_quota(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """
    检查用户 Token 配额
    
    如果配额不足抛出异常
    """
    token_manager = TokenManager(db)
    
    if not await token_manager.check_quota(user_id, required_tokens=50):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Token 配额不足，请升级会员或等待下月重置"
        )
    
    return True
