"""学习计划 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.db.session import get_db
from app.schemas.plan import PlanResponse, TaskResponse
from app.schemas.common import DataResponse
from app.services.plan_service import PlanService
from app.dependencies import get_current_user_id
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("api.plan")


class GeneratePlanRequest(BaseModel):
    """生成计划请求"""
    plan_data: Dict[str, Any]


@router.get("/current", response_model=DataResponse)
async def get_current_plan(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取当前学习计划"""
    service = PlanService(db)
    plan = await service.get_current_plan(user_id)
    
    if not plan:
        return DataResponse(
            code="success",
            data={"has_plan": False, "message": "暂无学习计划"}
        )
    
    return DataResponse(
        code="success",
        data={
            "has_plan": True,
            **plan
        }
    )


@router.post("/generate", response_model=DataResponse)
async def generate_plan(
    request: GeneratePlanRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    基于 AI 生成的数据创建学习计划
    
    接收 AI 返回的计划数据，创建完整的数据库记录
    """
    logger.info(f"用户 {user_id} 请求生成学习计划")
    
    service = PlanService(db)
    
    try:
        plan = await service.create_plan_from_ai(user_id, request.plan_data)
        
        return DataResponse(
            code="success",
            message="学习计划创建成功",
            data={
                "plan_id": plan.id,
                "title": plan.title,
                "start_date": plan.start_date.isoformat() if plan.start_date else None,
                "end_date": plan.end_date.isoformat() if plan.end_date else None
            }
        )
    except Exception as e:
        logger.error(f"生成计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/today", response_model=DataResponse)
async def get_today_tasks(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取今日任务"""
    service = PlanService(db)
    tasks = await service.get_today_tasks(user_id)
    
    return DataResponse(
        code="success",
        data={"tasks": tasks, "count": len(tasks)}
    )


@router.get("/tasks/week", response_model=DataResponse)
async def get_week_tasks(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取本周任务"""
    service = PlanService(db)
    tasks = await service.get_week_tasks(user_id)
    
    return DataResponse(
        code="success",
        data={"tasks": tasks, "count": len(tasks)}
    )


@router.post("/task/{task_id}/complete", response_model=DataResponse)
async def complete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """完成任务打卡"""
    logger.info(f"完成任务: {task_id}, user={user_id}")
    
    service = PlanService(db)
    
    try:
        result = await service.complete_task(task_id, user_id)
        
        return DataResponse(
            code="success",
            message="任务完成！",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"完成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/task/{task_id}/skip", response_model=DataResponse)
async def skip_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """跳过任务"""
    logger.info(f"跳过任务: {task_id}, user={user_id}")
    
    service = PlanService(db)
    
    success = await service.skip_task(task_id, user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="操作失败")
    
    return DataResponse(
        code="success",
        message="任务已跳过"
    )


@router.get("/task/{task_id}", response_model=DataResponse)
async def get_task_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """获取任务详情"""
    from sqlalchemy import select
    from app.models.task import DailyTask
    from app.models.plan import StudyPlan
    
    stmt = select(DailyTask).where(DailyTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限
    plan_stmt = select(StudyPlan).where(StudyPlan.id == task.plan_id)
    plan_result = await db.execute(plan_stmt)
    plan = plan_result.scalar_one_or_none()
    
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权限")
    
    return DataResponse(
        code="success",
        data={
            "id": task.id,
            "title": task.title,
            "content": task.content,
            "duration_mins": task.duration_mins,
            "difficulty": task.difficulty,
            "status": task.status,
            "scheduled_date": task.scheduled_date.isoformat() if task.scheduled_date else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "score": task.score
        }
    )
