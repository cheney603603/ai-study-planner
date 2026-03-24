"""用户模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String(20), unique=True, index=True, nullable=False)
    nickname = Column(String(50))
    avatar_url = Column(String(500))
    level = Column(String(20), default="入门")  # 入门/进阶/大师/宗师
    total_score = Column(Integer, default=0)   # 总积分
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    plans = relationship("StudyPlan", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    sessions = relationship("ChatSession", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.phone}>"
