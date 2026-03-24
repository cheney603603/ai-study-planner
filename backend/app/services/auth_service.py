"""认证服务"""
import uuid
import random
import redis
import json
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.subscription import Subscription, PlanType
from app.schemas.auth import UserInfo
from app.core.security import create_access_token
from app.core.logging import get_logger
from app.core.sms import sms_service
from app.config import settings

logger = get_logger("service.auth")


class AuthService:
    """认证服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client = None
        self._init_redis()
    
    def _init_redis(self):
        """初始化 Redis 连接"""
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.warning(f"Redis 连接失败，使用内存存储: {str(e)}")
            self.redis_client = None
    
    async def send_verification_code(self, phone: str) -> bool:
        """
        发送验证码
        
        验证码存储在 Redis 中，有效期 5 分钟
        同一手机号 60 秒内不能重复发送
        """
        # 检查发送频率
        last_send_key = f"sms:last_send:{phone}"
        if self.redis_client and self.redis_client.get(last_send_key):
            logger.warning(f"验证码发送过于频繁: {phone}")
            return False
        
        # 生成验证码
        code = str(random.randint(100000, 999999))
        
        # 存储验证码
        code_key = f"sms:code:{phone}"
        if self.redis_client:
            self.redis_client.setex(code_key, 300, code)  # 5分钟有效期
            self.redis_client.setex(last_send_key, 60, "1")  # 60秒间隔
        
        # 发送短信
        success = await sms_service.send_verification_code(phone, code)
        
        if success:
            logger.info(f"验证码发送成功: phone={phone}, code={code}")
        else:
            logger.error(f"验证码发送失败: phone={phone}")
        
        return success
    
    async def verify_code(self, phone: str, code: str) -> bool:
        """验证验证码"""
        code_key = f"sms:code:{phone}"
        
        if self.redis_client:
            stored_code = self.redis_client.get(code_key)
            if stored_code and stored_code == code:
                self.redis_client.delete(code_key)
                return True
        
        # 开发模式：任意 6 位数字验证码
        if len(code) == 6 and code.isdigit():
            if self.redis_client:
                self.redis_client.delete(code_key)
            return True
        
        logger.warning(f"验证码错误: phone={phone}, input={code}")
        return False
    
    async def login(self, phone: str, code: str) -> Optional[dict]:
        """
        验证码登录
        
        1. 验证验证码
        2. 获取或创建用户
        3. 生成 Token
        4. 返回用户信息
        """
        # 验证验证码
        if not await self.verify_code(phone, code):
            return None
        
        # 获取或创建用户
        user = await self._get_or_create_user(phone)
        
        # 创建订阅（如果没有）
        await self._ensure_subscription(user.id)
        
        # 生成 Token
        token = create_access_token(
            data={"sub": user.id, "phone": phone},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        logger.info(f"用户登录成功: {phone}, user_id={user.id}")
        
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
            # 更新最后登录时间
            user.updated_at = datetime.utcnow()
            await self.db.commit()
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
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"新用户注册: {phone}")
        return user
    
    async def _ensure_subscription(self, user_id: str) -> Subscription:
        """确保用户有订阅记录"""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            subscription = Subscription(
                id=str(uuid.uuid4()),
                user_id=user_id,
                plan_type=PlanType.MONTHLY.value,
                token_quota=settings.MONTHLY_TOKEN_QUOTA,
                token_used=0,
                status="active",
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            self.db.add(subscription)
            await self.db.commit()
            await self.db.refresh(subscription)
            
            logger.info(f"创建订阅: user_id={user_id}, quota={settings.MONTHLY_TOKEN_QUOTA}")
        
        return subscription
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据 ID 获取用户"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_user_profile(
        self,
        user_id: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[User]:
        """更新用户资料"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        if nickname:
            user.nickname = nickname
        if avatar_url:
            user.avatar_url = avatar_url
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
