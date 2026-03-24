"""任务模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class DailyTask(Base):
    """每日任务表"""
    __tablename__ = "daily_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("study_plans.id"), nullable=False)
    phase_id = Column(String(36), ForeignKey("plan_phases.id"))
    title = Column(String(200), nullable=False)
    content = Column(Text)  # 任务详细描述
    duration_mins = Column(Integer)  # 预计时长（分钟）
    difficulty = Column(String(20), default="medium")  # easy/medium/hard
    status = Column(String(20), default="pending")  # pending/completed/skip
    scheduled_date = Column(DateTime)  # 计划日期
    completed_at = Column(DateTime)  # 完成时间
    score = Column(Integer, default=10)  # 完成任务获得的积分
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    plan = relationship("StudyPlan", back_populates="tasks")
    
    async def complete(self):
        """完成任务"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<DailyTask {self.title}>"
