"""订阅服务测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.subscription_service import SubscriptionService


class TestSubscriptionService:
    """订阅服务测试"""

    @pytest.mark.asyncio
    async def test_get_available_plans(self):
        """测试获取可用方案"""
        mock_db = AsyncMock()
        service = SubscriptionService.__new__(SubscriptionService)
        service.db = mock_db
        service.token_manager = MagicMock()

        plans = await service.get_available_plans()

        assert len(plans) == 2
        assert plans[0]["id"] == "monthly"
        assert plans[1]["id"] == "yearly"
        assert plans[0]["token_quota"] == 100000
        assert plans[1]["token_quota"] == 1000000

    @pytest.mark.asyncio
    async def test_get_user_subscription_none(self):
        """测试获取无订阅用户"""
        mock_db = AsyncMock()
        service = SubscriptionService.__new__(SubscriptionService)
        service.token_manager = MagicMock()
        service.token_manager.get_usage_info = AsyncMock(
            return_value={"has_subscription": False}
        )

        result = await service.get_user_subscription("user123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_subscription_exists(self):
        """测试获取已有订阅"""
        mock_db = AsyncMock()
        service = SubscriptionService.__new__(SubscriptionService)
        service.token_manager = MagicMock()
        service.token_manager.get_usage_info = AsyncMock(
            return_value={
                "has_subscription": True,
                "plan_type": "monthly",
                "quota": 100000,
                "used": 50000,
                "remaining": 50000,
                "usage_percentage": 50.0,
                "expires_at": "2025-04-01T00:00:00",
            }
        )

        result = await service.get_user_subscription("user123")
        assert result is not None
        assert result["plan_type"] == "monthly"
        assert result["remaining"] == 50000
