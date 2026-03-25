"""任务模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.db.base import Base


class DailyTask(Base):
    """每日任务表"""
    __tablename__ = "daily_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("study_plans.id"), nullable=False, index=True)
    phase_id = Column(String(36), ForeignKey("plan_phases.id"), index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    duration_mins = Column(Integer)
    difficulty = Column(String(20), default="medium")
    status = Column(String(20), default="pending", index=True)   # 高频过滤字段
    scheduled_date = Column(DateTime, index=True)                # 高频查询字段
    completed_at = Column(DateTime)
    score = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 复合索引：按计划+日期查询今日任务
    __table_args__ = (
        Index("ix_daily_tasks_plan_date", "plan_id", "scheduled_date"),
        Index("ix_daily_tasks_plan_status", "plan_id", "status"),
    )

    # 关系
    plan = relationship("StudyPlan", back_populates="tasks")

    async def complete(self):
        """完成任务"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()

    def __repr__(self):
        return f"<DailyTask {self.title}>"
