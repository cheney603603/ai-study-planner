"""认证服务"""
import uuid
import random
import redis
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.subscription import Subscription, PlanType
from app.schemas.auth import UserInfo
from app.core.security import create_access_token
from app.core.logging import get_logger
from app.config import settings

logger = get_logger("service.auth")

# Redis 客户端（用于存储验证码）
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


class AuthService:
    """认证服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def send_verification_code(self, phone: str) -> bool:
        """
        发送验证码
        
        验证码存储在 Redis 中，有效期 5 分钟
        同一手机号 60 秒内不能重复发送
        """
        # 检查发送频率
        last_send_key = f"sms:last_send:{phone}"
        if redis_client.get(last_send_key):
            logger.warning(f"验证码发送过于频繁: {phone}")
            return False
        
        # 生成验证码
        code = str(random.randint(100000, 999999))
        
        # 存储验证码
        code_key = f"sms:code:{phone}"
        redis_client.setex(code_key, 300, code)  # 5分钟有效期
        
        # 设置发送间隔
        redis_client.setex(last_send_key, 60, "1")  # 60秒间隔
        
        # TODO: 实际发送短信（这里打印日志，生产环境调用阿里云短信API）
        logger.info(f"验证码已发送 (开发环境): 手机号={phone}, 验证码={code}")
        
        return True
    
    async def login(self, phone: str, code: str) -> dict:
        """
        验证码登录
        
        1. 验证验证码
        2. 获取或创建用户
        3. 生成 Token
        4. 返回用户信息
        """
        # 验证验证码
        code_key = f"sms:code:{phone}"
        stored_code = redis_client.get(code_key)
        
        if not stored_code or stored_code != code:
            logger.warning(f"验证码错误: phone={phone}, input={code}")
            return None
        
        # 删除已使用的验证码
        redis_client.delete(code_key)
        
        # 获取或创建用户
        user = await self._get_or_create_user(phone)
        
        # 创建订阅（如果没有）
        await self._ensure_subscription(user.id)
        
        # 生成 Token
        token = create_access_token(
            data={"sub": user.id, "phone": phone},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        logger.info(f"用户登录成功: {phone}")
        
        return {
            "access_token": token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": UserInfo(
                id=user.id,
                phone=user.phone,
                nickname=user.nickname,
                avatar_url=user.avatar_url,
                level=user.level,
                total_score=user.total_score
            )
        }
    
    async def _get_or_create_user(self, phone: str) -> User:
        """获取或创建用户"""
        # 查询用户
        stmt = select(User).where(User.phone == phone)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            return user
        
        # 创建新用户
        user = User(
            id=str(uuid.uuid4()),
            phone=phone,
            nickname=f"用户{phone[-4:]}",
            level="入门",
            total_score=0
        )
        self.db.add(user)
        await self.db.flush()
        
        logger.info(f"新用户注册: {phone}")
        return user
    
    async def _ensure_subscription(self, user_id: str) -> Subscription:
        """确保用户有订阅记录"""
        from sqlalchemy import select
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            subscription = Subscription(
                user_id=user_id,
                plan_type=PlanType.MONTHLY.value,
                token_quota=settings.MONTHLY_TOKEN_QUOTA,
                token_used=0,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            self.db.add(subscription)
            await self.db.flush()
        
        return subscription
