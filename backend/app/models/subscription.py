"""订阅模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class PlanType(str, enum.Enum):
    """订阅方案类型"""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Subscription(Base):
    """订阅表"""
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    plan_type = Column(String(20), default=PlanType.MONTHLY.value)
    token_quota = Column(Integer, default=100000)    # Token 配额
    token_used = Column(Integer, default=0)          # 已用 Token
    status = Column(String(20), default="active")    # active/expired/cancelled
    starts_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="subscription")
    
    @property
    def token_remaining(self) -> int:
        """剩余 Token"""
        return max(0, self.token_quota - self.token_used)
    
    def __repr__(self):
        return f"<Subscription {self.user_id} - {self.plan_type}>"
