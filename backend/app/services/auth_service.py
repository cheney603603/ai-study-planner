"""认证服务"""
import uuid
import random
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

# 尝试导入 redis，失败时降级
try:
    import redis as _redis_lib
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


class AuthService:
    """认证服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """初始化 Redis 连接"""
        if not _REDIS_AVAILABLE:
            logger.warning("redis 包未安装，使用内存降级模式")
            return
        try:
            client = _redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
            client.ping()
            self.redis_client = client
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.warning(f"Redis 连接失败，使用内存降级模式: {e}")

    # ------------------------------------------------------------------ #
    # 验证码
    # ------------------------------------------------------------------ #

    async def send_verification_code(self, phone: str) -> bool:
        """
        发送验证码
        - Redis 可用：存储到 Redis，5 分钟有效，60 秒限频
        - Redis 不可用：开发模式打印验证码，不实际发送
        """
        # 限频检查
        last_send_key = f"sms:last_send:{phone}"
        if self.redis_client and self.redis_client.get(last_send_key):
            logger.warning(f"验证码发送过于频繁: {phone}")
            return False

        code = str(random.randint(100000, 999999))

        if self.redis_client:
            code_key = f"sms:code:{phone}"
            self.redis_client.setex(code_key, 300, code)
            self.redis_client.setex(last_send_key, 60, "1")
            success = await sms_service.send_verification_code(phone, code)
        else:
            # 无 Redis：仅在 DEBUG 模式下允许降级
            if not settings.DEBUG:
                logger.error("生产环境 Redis 不可用，拒绝发送验证码")
                return False
            logger.info(f"[DEV] 验证码: phone={phone}, code={code}")
            success = True

        if success:
            logger.info(f"验证码发送成功: phone={phone}")
        else:
            logger.error(f"验证码发送失败: phone={phone}")
        return success

    async def verify_code(self, phone: str, code: str) -> bool:
        """
        验证验证码
        - Redis 可用：严格校验
        - Redis 不可用 + DEBUG：任意 6 位数字通过（仅开发环境）
        """
        code_key = f"sms:code:{phone}"

        if self.redis_client:
            stored_code = self.redis_client.get(code_key)
            if stored_code and stored_code == code:
                self.redis_client.delete(code_key)
                return True
            logger.warning(f"验证码错误: phone={phone}")
            return False

        # 无 Redis 降级：仅 DEBUG 模式允许
        if settings.DEBUG and len(code) == 6 and code.isdigit():
            logger.warning(f"[DEV] 跳过验证码校验: phone={phone}")
            return True

        logger.warning(f"验证码校验失败（Redis 不可用且非 DEBUG）: phone={phone}")
        return False

    # ------------------------------------------------------------------ #
    # 登录
    # ------------------------------------------------------------------ #

    async def login(self, phone: str, code: str) -> Optional[dict]:
        """验证码登录"""
        if not await self.verify_code(phone, code):
            return None

        user = await self._get_or_create_user(phone)
        await self._ensure_subscription(user.id)

        token = create_access_token(
            data={"sub": user.id, "phone": phone},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
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
                total_score=user.total_score,
            ),
        }

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #

    async def _get_or_create_user(self, phone: str) -> User:
        """获取或创建用户"""
        stmt = select(User).where(User.phone == phone)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.updated_at = datetime.utcnow()
            await self.db.commit()
            return user

        user = User(
            id=str(uuid.uuid4()),
            phone=phone,
            nickname=f"用户{phone[-4:]}",
            level="入门",
            total_score=0,
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
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            self.db.add(subscription)
            await self.db.commit()
            await self.db.refresh(subscription)
            logger.info(f"创建订阅: user_id={user_id}")

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
        avatar_url: Optional[str] = None,
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
