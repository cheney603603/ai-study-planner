"""学习计划 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.plan import PlanResponse, TaskResponse
from app.services.plan_service import PlanService
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("api.plan")


@router.get("/current")
async def get_current_plan(
    db: AsyncSession = Depends(get_db),
    user_id: str = "test-user-id"
):
    """获取当前学习计划"""
    service = PlanService(db)
    plan = await service.get_current_plan(user_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="暂无学习计划")
    
    return plan


@router.post("/generate")
async def generate_plan(
    db: AsyncSession = Depends(get_db),
    user_id: str = "test-user-id"
):
    """基于对话历史生成学习计划"""
    logger.info(f"用户 {user_id} 请求生成学习计划")
    
    service = PlanService(db)
    try:
        plan = await service.generate_plan_from_session(user_id)
        return {"code": "success", "plan": plan}
    except Exception as e:
        logger.error(f"生成计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/today")
async def get_today_tasks(
    db: AsyncSession = Depends(get_db),
    user_id: str = "test-user-id"
):
    """获取今日任务"""
    service = PlanService(db)
    tasks = await service.get_today_tasks(user_id)
    return {"tasks": tasks}


@router.get("/tasks/week")
async def get_week_tasks(
    db: AsyncSession = Depends(get_db),
    user_id: str = "test-user-id"
):
    """获取本周任务"""
    service = PlanService(db)
    tasks = await service.get_week_tasks(user_id)
    return {"tasks": tasks}


@router.post("/task/{task_id}/complete")
async def complete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """完成任务打卡"""
    logger.info(f"完成任务: {task_id}")
    
    service = PlanService(db)
    try:
        result = await service.complete_task(task_id)
        return {
            "code": "success",
            "score_earned": result.get("score", 0),
            "new_total_score": result.get("new_total_score", 0),
            "level_up": result.get("level_up"),
            "new_badges": result.get("new_badges", [])
        }
    except Exception as e:
        logger.error(f"完成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
