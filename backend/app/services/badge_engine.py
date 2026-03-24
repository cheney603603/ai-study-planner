"""徽章引擎"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
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

# 徽章定义
BADGE_DEFINITIONS = [
    {"code": "first_login", "name": "初来乍到", "description": "首次登录", "score": 50},
    {"code": "first_plan", "name": "计划达人", "description": "创建第一个学习计划", "score": 100},
    {"code": "first_task", "name": "行动派", "description": "完成第一个学习任务", "score": 50},
    {"code": "streak_3", "name": "三天打鱼", "description": "连续学习 3 天", "score": 100},
    {"code": "streak_7", "name": "周冠军", "description": "连续学习 7 天", "score": 200},
    {"code": "streak_30", "name": "月度之星", "description": "连续学习 30 天", "score": 500},
    {"code": "tasks_10", "name": "小试牛刀", "description": "完成 10 个任务", "score": 100},
    {"code": "tasks_50", "name": "熟能生巧", "description": "完成 50 个任务", "score": 300},
    {"code": "tasks_100", "name": "百炼成钢", "description": "完成 100 个任务", "score": 500},
    {"code": "level_enter", "name": "入门", "description": "达到入门等级", "score": 50},
    {"code": "level_advanced", "name": "进阶", "description": "达到进阶等级", "score": 150},
    {"code": "level_master", "name": "大师", "description": "达到大师等级", "score": 300},
    {"code": "level_master2", "name": "一代宗师", "description": "达到宗师等级", "score": 500},
    {"code": "score_500", "name": "积分小将", "description": "累计获得 500 积分", "score": 100},
    {"code": "score_2000", "name": "学分富户", "description": "累计获得 2000 积分", "score": 200},
]


class BadgeEngine:
    """徽章引擎 - 处理积分、徽章和等级"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._badge_cache = {}
    
    async def initialize_badges(self):
        """初始化徽章数据到数据库"""
        for badge_def in BADGE_DEFINITIONS:
            # 检查是否已存在
            stmt = select(Badge).where(Badge.code == badge_def["code"])
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                badge = Badge(
                    id=self._generate_id(),
                    name=badge_def["name"],
                    code=badge_def["code"],
                    description=badge_def["description"],
                    score=badge_def["score"]
                )
                self.db.add(badge)
        
        await self.db.commit()
        logger.info("徽章数据初始化完成")
    
    def _generate_id(self) -> str:
        import uuid
        return str(uuid.uuid4())
    
    def calculate_level(self, score: int) -> str:
        """根据积分计算等级"""
        for level in LEVELS:
            if level["min_score"] <= score <= level["max_score"]:
                return level["name"]
        return "入门"
    
    def check_level_up(self, user: User) -> Optional[Dict[str, str]]:
        """检查等级是否提升"""
        old_level = user.level
        new_level = self.calculate_level(user.total_score)
        
        if old_level != new_level:
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
                level_progress=next_level_info.get("progress", 100) if next_level_info else 100
            ),
            earned_badges=earned_badges,
            all_badges=all_badges
        )
    
    def _get_next_level_info(self, current_level: str, score: int) -> Optional[Dict[str, Any]]:
        """获取下一等级信息"""
        current_idx = next((i for i, l in enumerate(LEVELS) if l["name"] == current_level), 0)
        
        if current_idx >= len(LEVELS) - 1:
            return None
        
        next_level = LEVELS[current_idx + 1]
        score_in_level = score - LEVELS[current_idx]["min_score"]
        level_range = next_level["min_score"] - LEVELS[current_idx]["min_score"]
        progress = (score_in_level / level_range * 100) if level_range > 0 else 100
        
        return {
            "name": next_level["name"],
            "min_score": next_level["min_score"],
            "progress": min(progress, 100)
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
        
        if not badges:
            # 初始化徽章
            await self.initialize_badges()
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
    
    async def get_all_badges_with_status(self, user_id: str) -> Dict[str, Any]:
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
    
    async def check_and_award_badges(self, user_id: str, context: Dict[str, Any] = None) -> List[BadgeResponse]:
        """
        检查并发放徽章
        
        Args:
            user_id: 用户 ID
            context: 上下文信息，包含：
                - task_completed: 完成任务数
                - streak_days: 连续学习天数
                - total_score: 总积分
        """
        if context is None:
            context = {}
        
        new_badges = []
        
        # 获取用户已获得的徽章
        earned = await self._get_earned_badges(user_id)
        earned_codes = {b.code for b in earned}
        
        task_count = context.get("task_completed", 0)
        streak = context.get("streak_days", 0)
        total_score = context.get("total_score", 0)
        
        # 检查任务相关徽章
        if task_count >= 1 and "first_task" not in earned_codes:
            await self._award_badge(user_id, "first_task")
            new_badges.append("first_task")
        
        if task_count >= 10 and "tasks_10" not in earned_codes:
            await self._award_badge(user_id, "tasks_10")
            new_badges.append("tasks_10")
        
        if task_count >= 50 and "tasks_50" not in earned_codes:
            await self._award_badge(user_id, "tasks_50")
            new_badges.append("tasks_50")
        
        if task_count >= 100 and "tasks_100" not in earned_codes:
            await self._award_badge(user_id, "tasks_100")
            new_badges.append("tasks_100")
        
        # 检查连续学习徽章
        if streak >= 3 and "streak_3" not in earned_codes:
            await self._award_badge(user_id, "streak_3")
            new_badges.append("streak_3")
        
        if streak >= 7 and "streak_7" not in earned_codes:
            await self._award_badge(user_id, "streak_7")
            new_badges.append("streak_7")
        
        if streak >= 30 and "streak_30" not in earned_codes:
            await self._award_badge(user_id, "streak_30")
            new_badges.append("streak_30")
        
        # 检查积分徽章
        if total_score >= 500 and "score_500" not in earned_codes:
            await self._award_badge(user_id, "score_500")
            new_badges.append("score_500")
        
        if total_score >= 2000 and "score_2000" not in earned_codes:
            await self._award_badge(user_id, "score_2000")
            new_badges.append("score_2000")
        
        return new_badges
    
    async def _award_badge(self, user_id: str, badge_code: str) -> bool:
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
    
    async def award_badge(self, user_id: str, badge_code: str) -> bool:
        """手动发放徽章"""
        return await self._award_badge(user_id, badge_code)
