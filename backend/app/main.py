"""FastAPI 应用入口"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.v1.router import api_router

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    setup_logging()
    logger.info(f"启动 {settings.APP_NAME} (DEBUG={settings.DEBUG})...")

    # 初始化数据库表
    from app.db.session import init_db
    await init_db()
    logger.info("数据库表初始化完成")

    # 初始化徽章数据
    try:
        from app.db.session import AsyncSessionLocal
        from app.services.badge_engine import BadgeEngine
        async with AsyncSessionLocal() as db:
            engine = BadgeEngine(db)
            await engine.initialize_badges()
        logger.info("徽章数据初始化完成")
    except Exception as e:
        logger.warning(f"徽章初始化失败（非致命）: {e}")

    yield

    logger.info("应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    description="基于大模型和多智能体系统的个性化学习规划平台 API",
    version="0.1.0-alpha",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "error",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


# 注册 API 路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "0.1.0-alpha",
    }


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "0.1.0-alpha",
        "docs": "/docs" if settings.DEBUG else "disabled",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
