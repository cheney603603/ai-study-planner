"""学习计划模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base


class StudyPlan(Base):
    """学习计划表"""
    __tablename__ = "study_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="active")  # active/completed/paused/cancelled
    goals = Column(JSON)  # 学习目标
    habits = Column(JSON)  # 生活习惯
    knowledge_level = Column(String(20))  # 入门/进阶
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User", back_populates="plans")
    phases = relationship("PlanPhase", back_populates="plan", order_by="PlanPhase.order")
    tasks = relationship("DailyTask", back_populates="plan")
    
    def __repr__(self):
        return f"<StudyPlan {self.title}>"


class PlanPhase(Base):
    """计划阶段表"""
    __tablename__ = "plan_phases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("study_plans.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    duration_days = Column(Integer)  # 阶段持续天数
    goals = Column(JSON)  # 阶段目标
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    plan = relationship("StudyPlan", back_populates="phases")
    
    def __repr__(self):
        return f"<PlanPhase {self.name}>"
