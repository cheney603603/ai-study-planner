"""奖励 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.schemas.rewards import RewardsInfo, LeaderboardEntry
from app.schemas.common import DataResponse
from app.services.badge_engine import BadgeEngine
from app.models.user import User
from app.dependencies import get_current_user_id
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("api.rewards")


@router.get("/score", response_model=DataResponse)
async def get_rewards_info(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取用户奖励信息"""
    engine = BadgeEngine(db)
    info = await engine.get_user_rewards_info(user_id)
    
    return DataResponse(
        code="success",
        data=info.model_dump()
    )


@router.get("/badges", response_model=DataResponse)
async def get_badges(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取徽章列表"""
    engine = BadgeEngine(db)
    result = await engine.get_all_badges_with_status(user_id)
    
    return DataResponse(
        code="success",
        data=result
    )


@router.get("/leaderboard", response_model=DataResponse)
async def get_leaderboard(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取积分排行榜"""
    # 获取积分最高用户
    stmt = (
        select(User)
        .order_by(User.total_score.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    leaderboard = []
    for rank, user in enumerate(users, 1):
        leaderboard.append({
            "rank": rank,
            # 不暴露内部 user_id，只展示昵称和头像
            "nickname": user.nickname or f"用户{user.phone[-4:] if user.phone else '****'}",
            "avatar_url": user.avatar_url,
            "total_score": user.total_score,
            "level": user.level,
        })
    
    return DataResponse(
        code="success",
        data={"leaderboard": leaderboard}
    )


@router.get("/rank", response_model=DataResponse)
async def get_user_rank(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取用户排名"""
    # 计算排名
    # 获取比当前用户积分高的数量
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    
    if not user:
        return DataResponse(
            code="success",
            data={"rank": 0, "total_users": 0}
        )
    
    # 统计排名
    count_stmt = select(func.count(User.id)).where(User.total_score > user.total_score)
    count_result = await db.execute(count_stmt)
    higher_count = count_result.scalar() or 0
    
    rank = higher_count + 1
    
    # 总用户数
    total_stmt = select(func.count(User.id))
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0
    
    return DataResponse(
        code="success",
        data={
            "rank": rank,
            "total_users": total,
            "total_score": user.total_score,
            "level": user.level
        }
    )


@router.post("/badges/{badge_code}/award", response_model=DataResponse)
async def manual_award_badge(
    badge_code: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """手动发放徽章（测试用）"""
    engine = BadgeEngine(db)
    success = await engine.award_badge(user_id, badge_code)
    
    if success:
        return DataResponse(
            code="success",
            message="徽章发放成功"
        )
    else:
        return DataResponse(
            code="error",
            message="徽章发放失败或已获得"
        )
