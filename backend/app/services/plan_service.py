"""计划服务"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.plan import StudyPlan, PlanPhase, DailyTask
from app.models.user import User
from app.schemas.plan import PlanResponse, TaskResponse, PlanPhaseResponse
from app.services.badge_engine import BadgeEngine
from app.core.logging import get_logger

logger = get_logger("service.plan")


class PlanService:
    """计划服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.badge_engine = BadgeEngine(db)
    
    async def get_current_plan(self, user_id: str) -> Optional[dict]:
        """获取当前学习计划"""
        stmt = (
            select(StudyPlan)
            .where(
                StudyPlan.user_id == user_id,
                StudyPlan.status == "active"
            )
            .order_by(StudyPlan.created_at.desc())
        )
        result = await self.db.execute(stmt)
        plan = result.scalar_one_or_none()
        
        if not plan:
            return None
        
        # 计算完成率
        completion_rate = await self._calculate_completion_rate(plan.id)
        
        # 获取阶段信息
        phases = await self._get_plan_phases(plan.id)
        
        return {
            "id": plan.id,
            "title": plan.title,
            "description": plan.description,
            "status": plan.status,
            "goals": plan.goals,
            "habits": plan.habits,
            "knowledge_level": plan.knowledge_level,
            "start_date": plan.start_date,
            "end_date": plan.end_date,
            "phases": phases,
            "completion_rate": completion_rate
        }
    
    async def _calculate_completion_rate(self, plan_id: str) -> float:
        """计算计划完成率"""
        # 总任务数
        total_stmt = select(func.count(DailyTask.id)).where(DailyTask.plan_id == plan_id)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        if total == 0:
            return 0.0
        
        # 已完成任务数
        completed_stmt = select(func.count(DailyTask.id)).where(
            DailyTask.plan_id == plan_id,
            DailyTask.status == "completed"
        )
        completed_result = await self.db.execute(completed_stmt)
        completed = completed_result.scalar() or 0
        
        return round(completed / total, 2)
    
    async def _get_plan_phases(self, plan_id: str) -> List[dict]:
        """获取计划阶段"""
        stmt = (
            select(PlanPhase)
            .where(PlanPhase.plan_id == plan_id)
            .order_by(PlanPhase.order)
        )
        result = await self.db.execute(stmt)
        phases = result.scalars().all()
        
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "order": p.order,
                "duration_days": p.duration_days,
                "goals": p.goals
            }
            for p in phases
        ]
    
    async def generate_plan_from_session(self, user_id: str) -> dict:
        """
        基于会话历史生成学习计划
        
        TODO: 调用 AI Agent 生成计划
        """
        logger.info(f"为用户生成学习计划: {user_id}")
        
        # TODO: 从会话历史提取信息
        # TODO: 调用 Plan Agent 生成计划
        
        # 返回示例计划（开发阶段）
        return {
            "id": "example-plan-id",
            "title": "Python 入门学习计划",
            "description": "零基础学习 Python 编程",
            "status": "active",
            "phases": [
                {
                    "name": "第一阶段：基础语法",
                    "duration_days": 14,
                    "tasks": 20
                },
                {
                    "name": "第二阶段：函数和模块",
                    "duration_days": 14,
                    "tasks": 18
                }
            ],
            "daily_tasks": 3
        }
    
    async def get_today_tasks(self, user_id: str) -> List[dict]:
        """获取今日任务"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        stmt = (
            select(DailyTask)
            .join(StudyPlan, DailyTask.plan_id == StudyPlan.id)
            .where(
                StudyPlan.user_id == user_id,
                StudyPlan.status == "active",
                DailyTask.scheduled_date >= today,
                DailyTask.scheduled_date < tomorrow
            )
            .order_by(DailyTask.scheduled_date)
        )
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()
        
        return [
            {
                "id": t.id,
                "title": t.title,
                "content": t.content,
                "duration_mins": t.duration_mins,
                "difficulty": t.difficulty,
                "status": t.status,
                "score": t.score
            }
            for t in tasks
        ]
    
    async def get_week_tasks(self, user_id: str) -> List[dict]:
        """获取本周任务"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        next_week = today + timedelta(days=7)
        
        stmt = (
            select(DailyTask)
            .join(StudyPlan, DailyTask.plan_id == StudyPlan.id)
            .where(
                StudyPlan.user_id == user_id,
                StudyPlan.status == "active",
                DailyTask.scheduled_date >= today,
                DailyTask.scheduled_date < next_week
            )
            .order_by(DailyTask.scheduled_date)
        )
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()
        
        return [
            {
                "id": t.id,
                "title": t.title,
                "content": t.content,
                "duration_mins": t.duration_mins,
                "difficulty": t.difficulty,
                "status": t.status,
                "scheduled_date": t.scheduled_date,
                "score": t.score
            }
            for t in tasks
        ]
    
    async def complete_task(self, task_id: str) -> dict:
        """
        完成任务
        
        1. 更新任务状态
        2. 增加用户积分
        3. 检查等级提升
        4. 检查徽章解锁
        """
        # 获取任务
        stmt = select(DailyTask).where(DailyTask.id == task_id)
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        if task.status == "completed":
            raise ValueError("任务已完成")
        
        # 更新任务状态
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        
        # 获取用户
        plan_stmt = select(StudyPlan).where(StudyPlan.id == task.plan_id)
        plan_result = await self.db.execute(plan_stmt)
        plan = plan_result.scalar_one_or_none()
        
        if not plan:
            raise ValueError("计划不存在")
        
        user_stmt = select(User).where(User.id == plan.user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError("用户不存在")
        
        # 增加积分
        old_score = user.total_score
        user.total_score += task.score
        
        # 检查等级提升
        level_up = self.badge_engine.check_level_up(user)
        
        # 检查徽章
        new_badges = await self.badge_engine.check_and_award_badges(user.id)
        
        await self.db.commit()
        
        logger.info(
            f"任务完成: task={task_id}, "
            f"score_earned={task.score}, "
            f"new_total={user.total_score}"
        )
        
        return {
            "score": task.score,
            "new_total_score": user.total_score,
            "level_up": level_up,
            "new_badges": new_badges
        }
