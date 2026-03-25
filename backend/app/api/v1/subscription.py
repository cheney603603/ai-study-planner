"""订阅 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import TokenUsage
from app.schemas.common import DataResponse
from app.services.subscription_service import SubscriptionService
from app.services.token_manager import TokenManager
from app.dependencies import get_current_user_id
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("api.subscription")


@router.get("/plans", response_model=DataResponse)
async def get_subscription_plans():
    """获取订阅方案列表"""
    return DataResponse(
        code="success",
        data={"plans": [
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
        ]}
    )


@router.get("/current", response_model=DataResponse)
async def get_current_subscription(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取当前订阅"""
    service = SubscriptionService(db)
    subscription = await service.get_user_subscription(user_id)
    
    if not subscription:
        return DataResponse(
            code="success",
            data={
                "has_subscription": False,
                "message": "暂无订阅"
            }
        )
    
    return DataResponse(
        code="success",
        data={
            "has_subscription": True,
            **subscription
        }
    )


@router.get("/token-usage", response_model=DataResponse)
async def get_token_usage(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取 Token 使用情况"""
    token_manager = TokenManager(db)
    usage = await token_manager.get_usage_info(user_id)
    
    return DataResponse(
        code="success",
        data=usage
    )


@router.post("/subscribe", response_model=DataResponse)
async def create_subscription(
    plan_type: str = "monthly",
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    创建订阅（模拟支付）
    
    TODO: 接入真实支付（支付宝/微信）
    """
    logger.info(f"创建订阅请求: user={user_id}, plan={plan_type}")
    
    service = SubscriptionService(db)
    
    try:
        subscription = await service.create_subscription(user_id, plan_type)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="您已有订阅，无需重复购买"
            )
        
        return DataResponse(
            code="success",
            message="订阅创建成功",
            data={
                "subscription_id": subscription.id,
                "plan_type": subscription.plan_type,
                "token_quota": subscription.token_quota,
                "expires_at": subscription.expires_at
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"订阅创建失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="订阅创建失败"
        )


@router.post("/renew", response_model=DataResponse)
async def renew_subscription(
    plan_type: str = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """续费订阅"""
    logger.info(f"续费订阅请求: user={user_id}")
    
    service = SubscriptionService(db)
    
    try:
        subscription = await service.renew_subscription(user_id, plan_type)
        
        return DataResponse(
            code="success",
            message="续费成功",
            data={
                "subscription_id": subscription.id,
                "plan_type": subscription.plan_type,
                "token_quota": subscription.token_quota,
                "expires_at": subscription.expires_at
            }
        )
    except Exception as e:
        logger.error(f"续费失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="续费失败"
        )
