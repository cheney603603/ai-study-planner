"""
集成测试：认证 API
覆盖完整请求链路：HTTP 请求 → 路由 → 服务 → 数据库
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

import app.models.user
import app.models.subscription
import app.models.plan
import app.models.task
import app.models.badge

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.config import settings

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine):
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(test_db):
    """创建测试客户端，覆盖数据库依赖"""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ------------------------------------------------------------------ #
# 发送验证码
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_send_code_invalid_phone(client):
    """非法手机号应返回 422"""
    resp = await client.post("/api/v1/auth/send-code", json={"phone": "12345"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_send_code_valid_phone(client, monkeypatch):
    """合法手机号 + DEBUG 模式应返回 200"""
    monkeypatch.setattr(settings, "DEBUG", True)
    resp = await client.post("/api/v1/auth/send-code", json={"phone": "13800138000"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == "success"


# ------------------------------------------------------------------ #
# 登录
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_login_wrong_code(client, monkeypatch):
    """错误验证码应返回 401"""
    monkeypatch.setattr(settings, "DEBUG", False)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13800138000", "code": "000000"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_success_debug(client, monkeypatch):
    """DEBUG 模式任意 6 位数字验证码登录成功"""
    monkeypatch.setattr(settings, "DEBUG", True)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13900139000", "code": "123456"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == "success"
    assert "access_token" in data["data"]
    assert data["data"]["user"]["phone"] == "13900139000"


@pytest.mark.asyncio
async def test_login_invalid_phone_format(client):
    """非法手机号格式应返回 422"""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "abcdefghijk", "code": "123456"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_non_digit_code(client):
    """非数字验证码应返回 422"""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13800138000", "code": "abc123"}
    )
    assert resp.status_code == 422


# ------------------------------------------------------------------ #
# 认证保护接口
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_me_without_token_prod(client, monkeypatch):
    """生产模式无 Token 访问 /me 应返回 401"""
    monkeypatch.setattr(settings, "DEBUG", False)
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token(client, monkeypatch):
    """有效 Token 访问 /me 应返回用户信息"""
    monkeypatch.setattr(settings, "DEBUG", True)
    # 先登录获取 token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"phone": "13700137000", "code": "654321"}
    )
    token = login_resp.json()["data"]["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["phone"] == "13700137000"


# ------------------------------------------------------------------ #
# 健康检查
# ------------------------------------------------------------------ #

@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
