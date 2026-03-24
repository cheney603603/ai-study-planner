"""计划服务"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.plan import StudyPlan, PlanPhase, DailyTask
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.plan import PlanResponse, TaskResponse, PlanPhaseResponse
from app.services.badge_engine import BadgeEngine
from app.core.logging import get_logger
from app.config import settings

logger = get_logger("service.plan")


class PlanService:
    """计划服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.badge_engine = BadgeEngine(db)
    
    async def create_plan_from_ai(
        self,
        user_id: str,
        plan_data: Dict[str, Any]
    ) -> StudyPlan:
        """从 AI 生成的数据创建学习计划"""
        logger.info(f"为用户创建学习计划: user_id={user_id}")
        
        plan = StudyPlan(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=plan_data.get("title", "学习计划"),
            description=plan_data.get("target", ""),
            status="active",
            goals=plan_data.get("goals", {}),
            habits=plan_data.get("habits", {}),
            knowledge_level=plan_data.get("knowledge_level", "入门"),
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=plan_data.get("total_days", 30))
        )
        
        self.db.add(plan)
        
        phases_data = plan_data.get("phases", [])
        for i, phase_data in enumerate(phases_data):
            phase = PlanPhase(
                id=str(uuid.uuid4()),
                plan_id=plan.id,
                name=phase_data.get("name", f"阶段{i+1}"),
                description=phase_data.get("description", ""),
                order=i,
                duration_days=phase_data.get("duration_days", 7),
                goals=phase_data.get("goals", [])
            )
            self.db.add(phase)
            
            await self._create_phase_tasks(
                plan_id=plan.id,
                phase_id=phase.id,
                phase_data=phase_data,
                start_date=plan.start_date
            )
        
        await self.db.commit()
        await self.db.refresh(plan)
        
        logger.info(f"学习计划创建成功: plan_id={plan.id}")
        return plan
    
    async def _create_phase_tasks(
        self,
        plan_id: str,
        phase_id: str,
        phase_data: Dict[str, Any],
        start_date: datetime
    ):
        """为阶段创建每日任务"""
        duration_days = phase_data.get("duration_days", 7)
        daily_tasks_avg = phase_data.get("daily_tasks_avg", 2)
        
        phase_start = start_date
        
        for day in range(duration_days):
            scheduled_date = phase_start + timedelta(days=day)
            tasks_count = min(daily_tasks_avg, 3)
            
            for task_num in range(tasks_count):
                task = DailyTask(
                    id=str(uuid.uuid4()),
                    plan_id=plan_id,
                    phase_id=phase_id,
                    title=self._generate_task_title(phase_data.get("name", ""), day, task_num),
                    content=self._generate_task_content(phase_data.get("goals", []), task_num),
                    duration_mins=30,
                    difficulty="medium",
                    status="pending",
                    scheduled_date=scheduled_date,
                    score=10
                )
                self.db.add(task)
    
    def _generate_task_title(self, phase_name: str, day: int, task_num: int) -> str:
        topics = ["学习新知识点", "实践练习", "复习巩固", "完成小测验", "总结笔记"]
        topic = topics[task_num % len(topics)]
        return f"第{day+1}天 - {topic}"
    
    def _generate_task_content(self, goals: List[str], task_num: int) -> str:
        if not goals:
            return "完成当日学习任务"
        goal = goals[task_num % len(goals)] if goals else "完成学习目标"
        return f"深入学习：{goal}"
    
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
        
        phases_stmt = (
            select(PlanPhase)
            .where(PlanPhase.plan_id == plan.id)
            .order_by(PlanPhase.order)
        )
        phases_result = await self.db.execute(phases_stmt)
        phases = phases_result.scalars().all()
        
        completion_rate = await self._calculate_completion_rate(plan.id)
        
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
            "phases": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "order": p.order,
                    "duration_days": p.duration_days,
                    "goals": p.goals
                }
                for p in phases
            ],
            "completion_rate": completion_rate
        }
    
    async def _calculate_completion_rate(self, plan_id: str) -> float:
        """计算计划完成率"""
        total_stmt = select(func.count(DailyTask.id)).where(DailyTask.plan_id == plan_id)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        if total == 0:
            return 0.0
        
        completed_stmt = select(func.count(DailyTask.id)).where(
            DailyTask.plan_id == plan_id,
            DailyTask.status == "completed"
        )
        completed_result = await self.db.execute(completed_stmt)
        completed = completed_result.scalar() or 0
        
        return round(completed / total, 2)
    
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
                "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
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
                "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
                "score": t.score
            }
            for t in tasks
        ]
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户学习统计"""
        # 总完成任务数
        total_completed_stmt = select(func.count(DailyTask.id)).join(
            StudyPlan, DailyTask.plan_id == StudyPlan.id
        ).where(
            StudyPlan.user_id == user_id,
            DailyTask.status == "completed"
        )
        total_result = await self.db.execute(total_completed_stmt)
        total_completed = total_result.scalar() or 0
        
        # 连续学习天数（简化：统计有完成任务的连续天数）
        # 实际应该更复杂的计算
        streak = await self._calculate_streak(user_id)
        
        return {
            "total_completed": total_completed,
            "streak_days": streak
        }
    
    async def _calculate_streak(self, user_id: str) -> int:
        """计算连续学习天数"""
        # 获取最近完成的任务，按日期分组
        stmt = (
            select(DailyTask)
            .join(StudyPlan, DailyTask.plan_id == StudyPlan.id)
            .where(
                StudyPlan.user_id == user_id,
                DailyTask.status == "completed",
                DailyTask.completed_at.isnot(None)
            )
            .order_by(DailyTask.completed_at.desc())
        )
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()
        
        if not tasks:
            return 0
        
        # 简化：返回1（实际应该计算连续日期）
        return 1
    
    async def complete_task(
        self,
        task_id: str,
        user_id: str
    ) -> dict:
        """完成任务"""
        # 获取任务
        stmt = select(DailyTask).where(DailyTask.id == task_id)
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        if task.status == "completed":
            raise ValueError("任务已完成")
        
        # 获取计划
        plan_stmt = select(StudyPlan).where(StudyPlan.id == task.plan_id)
        plan_result = await self.db.execute(plan_stmt)
        plan = plan_result.scalar_one_or_none()
        
        if not plan or plan.user_id != user_id:
            raise ValueError("无权限操作此任务")
        
        # 更新任务状态
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        
        # 获取用户
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError("用户不存在")
        
        # 增加积分
        old_score = user.total_score
        user.total_score += task.score
        
        # 检查等级提升
        level_up = self.badge_engine.check_level_up(user)
        
        # 获取用户统计用于徽章检查
        stats = await self.get_user_stats(user_id)
        
        # 检查徽章
        new_badges = await self.badge_engine.check_and_award_badges(
            user_id,
            context={
                "task_completed": stats.get("total_completed", 0),
                "streak_days": stats.get("streak_days", 0),
                "total_score": user.total_score
            }
        )
        
        await self.db.commit()
        
        logger.info(
            f"任务完成: task={task_id}, "
            f"score_earned={task.score}, "
            f"new_total={user.total_score}"
        )
        
        return {
            "task_id": task_id,
            "score_earned": task.score,
            "new_total_score": user.total_score,
            "level_up": level_up,
            "new_badges": new_badges
        }
    
    async def skip_task(self, task_id: str, user_id: str) -> bool:
        """跳过任务"""
        stmt = select(DailyTask).where(DailyTask.id == task_id)
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        
        if not task:
            return False
        
        plan_stmt = select(StudyPlan).where(StudyPlan.id == task.plan_id)
        plan_result = await self.db.execute(plan_stmt)
        plan = plan_result.scalar_one_or_none()
        
        if not plan or plan.user_id != user_id:
            return False
        
        task.status = "skip"
        await self.db.commit()
        
        return True
