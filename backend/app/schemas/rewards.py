"""奖励系统模型"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class BadgeResponse(BaseModel):
    """徽章响应"""
    id: str
    name: str
    code: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    earned: bool = False
    earned_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LevelInfo(BaseModel):
    """等级信息"""
    current_level: str  # 当前等级
    next_level: Optional[str] = None  # 下一等级
    current_score: int  # 当前积分
    score_to_next_level: Optional[int] = None  # 距离下一级所需积分
    level_progress: float = 0.0  # 进度百分比


class RewardsInfo(BaseModel):
    """奖励信息"""
    total_score: int
    level_info: LevelInfo
    earned_badges: List[BadgeResponse] = []
    all_badges: List[BadgeResponse] = []


class LeaderboardEntry(BaseModel):
    """排行榜条目"""
    rank: int
    user_id: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    total_score: int
    level: str
