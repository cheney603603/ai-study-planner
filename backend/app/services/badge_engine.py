"""徽章引擎"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.badge import Badge, UserBadge
from app.models.user import User
from app.schemas.rewards import BadgeResponse, LevelInfo, RewardsInfo
from app.core.logging import get_logger

logger = get_logger("service.badge")

# 等级定义
LEVELS = [
    {"name": "入门", "min_score": 0, "max_score": 499},
    {"name": "进阶", "min_score": 500, "max_score": 1999},
    {"name": "大师", "min_score": 2000, "max_score": 4999},
    {"name": "宗师", "min_score": 5000, "max_score": 999999}
]


class BadgeEngine:
    """徽章引擎"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def calculate_level(self, score: int) -> str:
        """根据积分计算等级"""
        for level in LEVELS:
            if level["min_score"] <= score <= level["max_score"]:
                return level["name"]
        return "入门"
    
    def check_level_up(self, user: User) -> Optional[dict]:
        """检查等级是否提升"""
        old_level = user.level
        new_level = self.calculate_level(user.total_score)
        
        if old_level != new_level:
            user.level = new_level
            logger.info(f"用户等级提升: {user.id}, {old_level} -> {new_level}")
            return {"old": old_level, "new": new_level}
        
        return None
    
    async def get_user_rewards_info(self, user_id: str) -> RewardsInfo:
        """获取用户奖励信息"""
        # 获取用户
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return RewardsInfo(
                total_score=0,
                level_info=LevelInfo(
                    current_level="入门",
                    current_score=0
                ),
                earned_badges=[],
                all_badges=[]
            )
        
        # 获取等级信息
        current_level = self.calculate_level(user.total_score)
        next_level_info = self._get_next_level_info(current_level, user.total_score)
        
        # 获取徽章
        earned_badges = await self._get_earned_badges(user_id)
        all_badges = await self._get_all_badges()
        
        return RewardsInfo(
            total_score=user.total_score,
            level_info=LevelInfo(
                current_level=current_level,
                next_level=next_level_info.get("name") if next_level_info else None,
                current_score=user.total_score,
                score_to_next_level=next_level_info.get("min_score") - user.total_score if next_level_info else None,
                level_progress=next_level_info.get("progress", 0) if next_level_info else 100
            ),
            earned_badges=earned_badges,
            all_badges=all_badges
        )
    
    def _get_next_level_info(self, current_level: str, score: int) -> Optional[dict]:
        """获取下一等级信息"""
        current_idx = next((i for i, l in enumerate(LEVELS) if l["name"] == current_level), 0)
        
        if current_idx >= len(LEVELS) - 1:
            return None
        
        next_level = LEVELS[current_idx + 1]
        progress = (score - LEVELS[current_idx]["min_score"]) / (next_level["min_score"] - LEVELS[current_idx]["min_score"])
        
        return {
            "name": next_level["name"],
            "min_score": next_level["min_score"],
            "progress": min(progress * 100, 100)
        }
    
    async def _get_earned_badges(self, user_id: str) -> List[BadgeResponse]:
        """获取用户已获得的徽章"""
        stmt = (
            select(Badge, UserBadge)
            .join(UserBadge, Badge.id == UserBadge.badge_id)
            .where(UserBadge.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        return [
            BadgeResponse(
                id=badge.id,
                name=badge.name,
                code=badge.code,
                description=badge.description,
                icon_url=badge.icon_url,
                earned=True,
                earned_at=user_badge.earned_at
            )
            for badge, user_badge in rows
        ]
    
    async def _get_all_badges(self) -> List[BadgeResponse]:
        """获取所有徽章"""
        stmt = select(Badge)
        result = await self.db.execute(stmt)
        badges = result.scalars().all()
        
        return [
            BadgeResponse(
                id=b.id,
                name=b.name,
                code=b.code,
                description=b.description,
                icon_url=b.icon_url,
                earned=False
            )
            for b in badges
        ]
    
    async def get_all_badges_with_status(self, user_id: str) -> dict:
        """获取所有徽章及其获得状态"""
        all_badges = await self._get_all_badges()
        earned = await self._get_earned_badges(user_id)
        earned_ids = {b.id for b in earned}
        
        return {
            "earned": earned,
            "all": [
                BadgeResponse(
                    id=b.id,
                    name=b.name,
                    code=b.code,
                    description=b.description,
                    icon_url=b.icon_url,
                    earned=b.id in earned_ids
                )
                for b in all_badges
            ]
        }
    
    async def check_and_award_badges(self, user_id: str) -> List[BadgeResponse]:
        """
        检查并发放徽章
        
        TODO: 根据用户行为触发徽章发放
        """
        # TODO: 实现徽章检查逻辑
        # - FIRST_LOGIN: 首次登录
        # - FIRST_PLAN: 创建首个计划
        # - FIRST_TASK: 完成首个任务
        # - STREAK_7: 连续学习 7 天
        # - STREAK_30: 连续学习 30 天
        # - LEVEL_ENTER: 入门
        # - LEVEL_ADVANCED: 进阶
        # - LEVEL_MASTER: 大师
        
        return []
    
    async def award_badge(self, user_id: str, badge_code: str) -> bool:
        """发放徽章"""
        # 获取徽章
        stmt = select(Badge).where(Badge.code == badge_code)
        result = await self.db.execute(stmt)
        badge = result.scalar_one_or_none()
        
        if not badge:
            logger.warning(f"徽章不存在: {badge_code}")
            return False
        
        # 检查是否已获得
        check_stmt = select(UserBadge).where(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge.id
        )
        check_result = await self.db.execute(check_stmt)
        if check_result.scalar_one_or_none():
            return False
        
        # 发放徽章
        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge.id,
            earned_at=datetime.utcnow()
        )
        self.db.add(user_badge)
        
        # 增加积分
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if user:
            user.total_score += badge.score
        
        await self.db.commit()
        
        logger.info(f"徽章发放成功: user={user_id}, badge={badge_code}")
        return True
