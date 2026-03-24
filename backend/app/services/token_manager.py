"""Token 配额管理服务"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import Subscription
from app.core.logging import get_logger
from app.core.exceptions import TokenQuotaExceededError

logger = get_logger("service.token")


class TokenManager:
    """Token 配额管理器"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_quota(self, user_id: str, required_tokens: int = 100) -> bool:
        """
        检查用户 Token 配额是否足够
        
        Args:
            user_id: 用户 ID
            required_tokens: 需要的 Token 数量
        
        Returns:
            bool: 配额是否足够
        """
        subscription = await self._get_subscription(user_id)
        
        if not subscription:
            logger.warning(f"用户无订阅记录: {user_id}")
            return False
        
        # 检查是否过期
        if subscription.expires_at < datetime.utcnow():
            logger.warning(f"订阅已过期: {user_id}, expires_at={subscription.expires_at}")
            return False
        
        remaining = subscription.token_quota - subscription.token_used
        return remaining >= required_tokens
    
    async def consume_tokens(self, user_id: str, tokens: int) -> dict:
        """
        消耗 Token
        
        Args:
            user_id: 用户 ID
            tokens: 消耗的 Token 数量
        
        Returns:
            dict: 消耗结果
        """
        subscription = await self._get_subscription(user_id)
        
        if not subscription:
            raise TokenQuotaExceededError("用户无订阅记录")
        
        # 检查配额
        if not await self.check_quota(user_id, tokens):
            remaining = subscription.token_quota - subscription.token_used
            raise TokenQuotaExceededError(
                f"Token 配额不足。剩余: {remaining}, 需要: {tokens}"
            )
        
        # 更新使用量
        new_used = subscription.token_used + tokens
        
        stmt = (
            update(Subscription)
            .where(Subscription.id == subscription.id)
            .values(
                token_used=new_used,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        logger.info(f"Token 消耗: user={user_id}, tokens={tokens}, total_used={new_used}")
        
        return {
            "tokens_consumed": tokens,
            "total_used": new_used,
            "remaining": subscription.token_quota - new_used,
            "quota": subscription.token_quota
        }
    
    async def get_usage_info(self, user_id: str) -> dict:
        """获取 Token 使用信息"""
        subscription = await self._get_subscription(user_id)
        
        if not subscription:
            return {
                "has_subscription": False,
                "quota": 0,
                "used": 0,
                "remaining": 0,
                "expires_at": None
            }
        
        return {
            "has_subscription": True,
            "plan_type": subscription.plan_type,
            "quota": subscription.token_quota,
            "used": subscription.token_used,
            "remaining": subscription.token_remaining,
            "expires_at": subscription.expires_at,
            "usage_percentage": round(subscription.token_used / subscription.token_quota * 100, 1) if subscription.token_quota > 0 else 0
        }
    
    async def reset_usage(self, user_id: str) -> bool:
        """重置 Token 使用量（月末/续费时）"""
        subscription = await self._get_subscription(user_id)
        
        if not subscription:
            return False
        
        stmt = (
            update(Subscription)
            .where(Subscription.id == subscription.id)
            .values(
                token_used=0,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        logger.info(f"Token 使用量重置: user={user_id}")
        return True
    
    async def upgrade_subscription(
        self,
        user_id: str,
        plan_type: str,
        extend_days: int = 30
    ) -> Subscription:
        """升级订阅方案"""
        from app.config import settings
        
        subscription = await self._get_subscription(user_id)
        
        if not subscription:
            # 创建新订阅
            subscription = Subscription(
                id=str(uuid.uuid4()),
                user_id=user_id,
                plan_type=plan_type,
                status="active"
            )
            self.db.add(subscription)
        
        # 设置配额
        if plan_type == "yearly":
            subscription.token_quota = settings.YEARLY_TOKEN_QUOTA
            extend_days = 365
        else:
            subscription.token_quota = settings.MONTHLY_TOKEN_QUOTA
        
        # 延长有效期
        if subscription.expires_at and subscription.expires_at > datetime.utcnow():
            subscription.expires_at = subscription.expires_at + timedelta(days=extend_days)
        else:
            subscription.expires_at = datetime.utcnow() + timedelta(days=extend_days)
        
        subscription.status = "active"
        subscription.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(subscription)
        
        logger.info(f"订阅升级: user={user_id}, plan={plan_type}")
        return subscription
    
    async def _get_subscription(self, user_id: str) -> Optional[Subscription]:
        """获取用户订阅"""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


# 导入 uuid
import uuid
