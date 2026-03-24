"""
测试：认证服务
覆盖：验证码发送/校验、登录、用户创建
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.auth_service import AuthService
from app.config import settings


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def auth_service(mock_db):
    svc = AuthService.__new__(AuthService)
    svc.db = mock_db
    svc.redis_client = None  # 无 Redis，走降级路径
    return svc


# ------------------------------------------------------------------ #
# 验证码
# ------------------------------------------------------------------ #

class TestVerifyCode:
    """验证码校验逻辑"""

    def test_dev_mode_any_6digit_passes(self, auth_service, monkeypatch):
        """DEBUG 模式下任意 6 位数字通过"""
        monkeypatch.setattr(settings, "DEBUG", True)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            auth_service.verify_code("13800138000", "123456")
        )
        assert result is True

    def test_dev_mode_non_6digit_fails(self, auth_service, monkeypatch):
        """DEBUG 模式下非 6 位数字不通过"""
        monkeypatch.setattr(settings, "DEBUG", True)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            auth_service.verify_code("13800138000", "12345")
        )
        assert result is False

    def test_prod_mode_no_redis_fails(self, auth_service, monkeypatch):
        """生产模式下无 Redis 时拒绝"""
        monkeypatch.setattr(settings, "DEBUG", False)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            auth_service.verify_code("13800138000", "123456")
        )
        assert result is False

    def test_redis_correct_code_passes(self, auth_service):
        """Redis 中存储的验证码匹配时通过"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "654321"
        mock_redis.delete = MagicMock()
        auth_service.redis_client = mock_redis

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            auth_service.verify_code("13800138000", "654321")
        )
        assert result is True
        mock_redis.delete.assert_called_once()

    def test_redis_wrong_code_fails(self, auth_service):
        """Redis 中存储的验证码不匹配时失败"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "654321"
        auth_service.redis_client = mock_redis

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            auth_service.verify_code("13800138000", "000000")
        )
        assert result is False


# ------------------------------------------------------------------ #
# 发送验证码
# ------------------------------------------------------------------ #

class TestSendCode:
    """发送验证码逻辑"""

    def test_prod_no_redis_returns_false(self, auth_service, monkeypatch):
        """生产模式无 Redis 时拒绝发送"""
        monkeypatch.setattr(settings, "DEBUG", False)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            auth_service.send_verification_code("13800138000")
        )
        assert result is False

    def test_dev_no_redis_returns_true(self, auth_service, monkeypatch):
        """DEBUG 模式无 Redis 时允许发送（打印验证码）"""
        monkeypatch.setattr(settings, "DEBUG", True)
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            auth_service.send_verification_code("13800138000")
        )
        assert result is True

    def test_redis_rate_limit(self, auth_service):
        """60 秒内重复发送被拒绝"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "1"  # 已发送标记存在
        auth_service.redis_client = mock_redis

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            auth_service.send_verification_code("13800138000")
        )
        assert result is False
