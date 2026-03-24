"""订阅 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import TokenUsage
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("api.subscription")


@router.get("/plans")
async def get_subscription_plans():
    """获取订阅方案列表"""
    return {
        "plans": [
            {
                "id": "monthly",
                "name": "月度会员",
                "description": "每月 100,000 Token",
                "price": 29.9,
                "token_quota": 100000,
                "duration_days": 30
            },
            {
                "id": "yearly",
                "name": "年度会员",
                "description": "每年 1,000,000 Token",
                "price": 299,
                "token_quota": 1000000,
                "duration_days": 365
            }
        ]
    }


@router.get("/current")
async def get_current_subscription(
    db: AsyncSession = Depends(get_db),
    user_id: str = None
):
    """获取当前订阅"""
    # TODO: 实现用户订阅查询
    return {
        "has_subscription": False,
        "plan": None
    }


@router.get("/token-usage", response_model=TokenUsage)
async def get_token_usage(
    db: AsyncSession = Depends(get_db),
    user_id: str = None
):
    """获取 Token 使用情况"""
    # TODO: 实现 Token 用量查询
    return TokenUsage(
        quota=100000,
        used=0,
        remaining=100000,
        reset_date="2026-04-01"
    )
