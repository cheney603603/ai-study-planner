"""徽章和聊天模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class Badge(Base):
    """徽章表"""
    __tablename__ = "badges"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)  # 徽章代码
    description = Column(Text)
    icon_url = Column(String(500))
    requirement = Column(JSON)  # 获得条件配置
    score = Column(Integer, default=100)  # 获得时奖励积分
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Badge {self.name}>"


class UserBadge(Base):
    """用户徽章关联表"""
    __tablename__ = "user_badges"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    badge_id = Column(String(36), ForeignKey("badges.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge")
    
    def __repr__(self):
        return f"<UserBadge user={self.user_id} badge={self.badge_id}>"


class ChatSession(Base):
    """聊天会话表"""
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("study_plans.id"))
    session_type = Column(String(30), default="goal_discussion")  # goal_discussion/plan_adjust/feedback
    status = Column(String(20), default="active")  # active/closed
    messages = Column(JSON)  # 消息历史
    context = Column(JSON, default=dict)  # 多轮对话上下文（collected_info 等）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<ChatSession {self.id}>"
