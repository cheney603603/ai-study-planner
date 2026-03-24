"""订阅服务测试"""
import pytest
from app.services.subscription_service import SubscriptionService


class TestSubscriptionService:
    """订阅服务测试"""
    
    @pytest.mark.asyncio
    async def test_get_available_plans(self):
        """测试获取可用方案"""
        mock_db = AsyncMock()
        service = SubscriptionService(mock_db)
        
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
        
        with patch.object(SubscriptionService, '__init__', lambda self, db: None):
            service = SubscriptionService(mock_db)
            service.token_manager = MagicMock()
            service.token_manager.get_usage_info = AsyncMock(return_value={
                "has_subscription": False
            })
            
            result = await service.get_user_subscription("user123")
            assert result is None
