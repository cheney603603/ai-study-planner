"""奖励 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.rewards import RewardsInfo, LeaderboardEntry
from app.services.badge_engine import BadgeEngine
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("api.rewards")


@router.get("/score", response_model=RewardsInfo)
async def get_rewards_info(
    db: AsyncSession = Depends(get_db),
    user_id: str = "test-user-id"
):
    """获取用户奖励信息"""
    engine = BadgeEngine(db)
    return await engine.get_user_rewards_info(user_id)


@router.get("/badges")
async def get_badges(
    db: AsyncSession = Depends(get_db),
    user_id: str = "test-user-id"
):
    """获取徽章列表"""
    engine = BadgeEngine(db)
    return await engine.get_all_badges_with_status(user_id)


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = 20
):
    """获取积分排行榜"""
    # TODO: 实现排行榜
    return {
        "leaderboard": [
            {"rank": 1, "user_id": "user1", "nickname": "学霸小明", "total_score": 5000, "level": "大师"},
            {"rank": 2, "user_id": "user2", "nickname": "学习达人", "total_score": 3500, "level": "大师"},
            {"rank": 3, "user_id": "user3", "nickname": "进步青年", "total_score": 2000, "level": "进阶"},
        ]
    }
