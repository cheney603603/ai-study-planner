"""学习计划相关模型"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GoalInfo(BaseModel):
    """学习目标信息"""
    subject: str = Field(..., description="学习科目/主题")
    target: str = Field(..., description="学习目标")
    reason: Optional[str] = Field(None, description="学习原因")
    deadline: Optional[str] = Field(None, description="期望完成时间")


class HabitInfo(BaseModel):
    """生活习惯信息"""
    daily_time_available: int = Field(..., description="每日可用学习时间（分钟）")
    preferred_learning_time: str = Field(default="morning", description="偏好学习时段")
    learning_style: List[str] = Field(default=["reading"], description="学习风格")


class PlanCreateRequest(BaseModel):
    """创建计划请求"""
    title: str = Field(..., min_length=1, max_length=200, description="计划标题")
    description: Optional[str] = None
    goals: Optional[GoalInfo] = None
    habits: Optional[HabitInfo] = None


class PlanPhaseResponse(BaseModel):
    """计划阶段响应"""
    id: str
    name: str
    description: Optional[str] = None
    order: int
    duration_days: int
    goals: Optional[dict] = None
    
    class Config:
        from_attributes = True


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    title: str
    content: Optional[str] = None
    duration_mins: int
    difficulty: str
    status: str
    scheduled_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: int
    
    class Config:
        from_attributes = True


class PlanResponse(BaseModel):
    """计划响应"""
    id: str
    title: str
    description: Optional[str] = None
    status: str
    goals: Optional[dict] = None
    habits: Optional[dict] = None
    knowledge_level: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    phases: List[PlanPhaseResponse] = []
    completion_rate: float = 0.0
    
    class Config:
        from_attributes = True


class TaskCompleteRequest(BaseModel):
    """完成任务请求"""
    task_id: str
    feedback: Optional[str] = Field(None, description="完成反馈")
