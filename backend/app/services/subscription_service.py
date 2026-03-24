"""订阅服务"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import Subscription, PlanType
from app.services.token_manager import TokenManager
from app.core.logging import get_logger
from app.config import settings

logger = get_logger("service.subscription")


class SubscriptionService:
    """订阅服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.token_manager = TokenManager(db)
    
    async def get_available_plans(self) -> List[dict]:
        """获取可用的订阅方案"""
        return [
            {
                "id": PlanType.MONTHLY.value,
                "name": "月度会员",
                "description": "每月 100,000 Token，支持 AI 学习规划",
                "price": 29.9,
                "original_price": 39.9,
                "token_quota": settings.MONTHLY_TOKEN_QUOTA,
                "duration_days": 30,
                "features": [
                    "AI 学习规划",
                    "无限任务打卡",
                    "积分徽章系统",
                    "基础学习内容"
                ]
            },
            {
                "id": PlanType.YEARLY.value,
                "name": "年度会员",
                "description": "每年 1,000,000 Token，超值优惠",
                "price": 299,
                "original_price": 399,
                "token_quota": settings.YEARLY_TOKEN_QUOTA,
                "duration_days": 365,
                "features": [
                    "月度会员全部功能",
                    "10倍 Token 配额",
                    "优先体验新功能",
                    "专属客服支持"
                ],
                "recommended": True
            }
        ]
    
    async def get_user_subscription(self, user_id: str) -> Optional[dict]:
        """获取用户当前订阅"""
        usage_info = await self.token_manager.get_usage_info(user_id)
        
        if not usage_info.get("has_subscription"):
            return None
        
        return {
            "plan_type": usage_info.get("plan_type"),
            "quota": usage_info.get("quota"),
            "used": usage_info.get("used"),
            "remaining": usage_info.get("remaining"),
            "usage_percentage": usage_info.get("usage_percentage"),
            "expires_at": usage_info.get("expires_at")
        }
    
    async def create_subscription(
        self,
        user_id: str,
        plan_type: str = PlanType.MONTHLY.value
    ) -> Subscription:
        """创建订阅"""
        # 检查是否已有订阅
        existing = await self.get_user_subscription(user_id)
        if existing:
            logger.info(f"用户已有订阅: {user_id}")
            return None
        
        # 确定配额和时长
        if plan_type == PlanType.YEARLY.value:
            quota = settings.YEARLY_TOKEN_QUOTA
            days = 365
        else:
            quota = settings.MONTHLY_TOKEN_QUOTA
            days = 30
        
        subscription = Subscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            plan_type=plan_type,
            token_quota=quota,
            token_used=0,
            status="active",
            expires_at=datetime.utcnow() + timedelta(days=days)
        )
        
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        logger.info(f"订阅创建成功: user={user_id}, plan={plan_type}")
        return subscription
    
    async def renew_subscription(
        self,
        user_id: str,
        plan_type: Optional[str] = None
    ) -> Subscription:
        """续费订阅"""
        from uuid import uuid4
        
        subscription_service = self  # 避免递归
        
        # 获取当前订阅
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            # 创建新订阅
            return await self.create_subscription(user_id, plan_type or PlanType.MONTHLY.value)
        
        # 确定续费参数
        if plan_type:
            subscription.plan_type = plan_type
            if plan_type == PlanType.YEARLY.value:
                subscription.token_quota = settings.YEARLY_TOKEN_QUOTA
                days = 365
            else:
                subscription.token_quota = settings.MONTHLY_TOKEN_QUOTA
                days = 30
        else:
            # 续费同类型
            if subscription.plan_type == PlanType.YEARLY.value:
                days = 365
            else:
                days = 30
        
        # 延长有效期
        if subscription.expires_at and subscription.expires_at > datetime.utcnow():
            subscription.expires_at = subscription.expires_at + timedelta(days=days)
        else:
            subscription.expires_at = datetime.utcnow() + timedelta(days=days)
        
        # 重置使用量
        subscription.token_used = 0
        subscription.status = "active"
        subscription.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        logger.info(f"订阅续费成功: user={user_id}, plan={subscription.plan_type}")
        return subscription


# 导入 uuid
import uuid
