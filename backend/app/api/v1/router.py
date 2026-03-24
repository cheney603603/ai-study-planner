"""API v1 路由注册"""
from fastapi import APIRouter
from app.api.v1 import auth, subscription, chat, plan, rewards

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(subscription.router, prefix="/subscription", tags=["会员"])
api_router.include_router(chat.router, prefix="/chat", tags=["对话"])
api_router.include_router(plan.router, prefix="/plan", tags=["学习计划"])
api_router.include_router(rewards.router, prefix="/rewards", tags=["奖励"])
