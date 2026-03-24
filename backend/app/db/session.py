"""数据库会话管理"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

# SQLite 不支持连接池参数，需要区分处理
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表（开发/测试环境使用）"""
    from app.db.base import Base
    # 导入所有模型，确保 metadata 中有表定义
    import app.models.user          # noqa: F401
    import app.models.subscription  # noqa: F401
    import app.models.plan          # noqa: F401
    import app.models.task          # noqa: F401
    import app.models.badge         # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
