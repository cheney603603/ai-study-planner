"""Token 管理器测试"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from app.services.token_manager import TokenManager


class TestTokenManager:

    @pytest.mark.asyncio
    async def test_check_quota_sufficient(self):
        """配额充足时返回 True"""
        mock_db = AsyncMock()
        mock_sub = MagicMock()
        mock_sub.token_quota = 100000
        mock_sub.token_used = 50000
        mock_sub.expires_at = datetime.utcnow() + timedelta(days=1)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                TokenManager, "_get_subscription",
                AsyncMock(return_value=mock_sub)
            )
            manager = TokenManager(mock_db)
            result = await manager.check_quota("user123", required_tokens=100)
            assert result is True

    @pytest.mark.asyncio
    async def test_check_quota_insufficient(self):
        """配额不足时返回 False"""
        mock_db = AsyncMock()
        mock_sub = MagicMock()
        mock_sub.token_quota = 100
        mock_sub.token_used = 100
        mock_sub.expires_at = datetime.utcnow() + timedelta(days=1)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                TokenManager, "_get_subscription",
                AsyncMock(return_value=mock_sub)
            )
            manager = TokenManager(mock_db)
            result = await manager.check_quota("user123", required_tokens=100)
            assert result is False

    @pytest.mark.asyncio
    async def test_check_quota_expired(self):
        """订阅过期时返回 False"""
        mock_db = AsyncMock()
        mock_sub = MagicMock()
        mock_sub.token_quota = 100000
        mock_sub.token_used = 0
        mock_sub.expires_at = datetime.utcnow() - timedelta(days=1)  # 已过期

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                TokenManager, "_get_subscription",
                AsyncMock(return_value=mock_sub)
            )
            manager = TokenManager(mock_db)
            result = await manager.check_quota("user123", required_tokens=100)
            assert result is False

    @pytest.mark.asyncio
    async def test_check_quota_no_subscription(self):
        """无订阅记录返回 False"""
        mock_db = AsyncMock()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                TokenManager, "_get_subscription",
                AsyncMock(return_value=None)
            )
            manager = TokenManager(mock_db)
            result = await manager.check_quota("user123", required_tokens=100)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_usage_info_no_subscription(self):
        """无订阅时返回正确格式"""
        mock_db = AsyncMock()
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                TokenManager, "_get_subscription",
                AsyncMock(return_value=None)
            )
            manager = TokenManager(mock_db)
            info = await manager.get_usage_info("user123")
            assert info["has_subscription"] is False
            assert info["remaining"] == 0

    @pytest.mark.asyncio
    async def test_get_usage_info_with_subscription(self):
        """有订阅时返回完整信息"""
        mock_db = AsyncMock()
        mock_sub = MagicMock()
        mock_sub.plan_type = "monthly"
        mock_sub.token_quota = 100000
        mock_sub.token_used = 30000
        mock_sub.expires_at = datetime.utcnow() + timedelta(days=15)

        # Mock property
        type(mock_sub).token_remaining = property(lambda self: 70000)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                TokenManager, "_get_subscription",
                AsyncMock(return_value=mock_sub)
            )
            manager = TokenManager(mock_db)
            info = await manager.get_usage_info("user123")
            assert info["has_subscription"] is True
            assert info["quota"] == 100000
            assert info["used"] == 30000
            assert info["usage_percentage"] == 30.0
