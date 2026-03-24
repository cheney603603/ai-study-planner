"""用户服务单元测试"""
import pytest
from app.services.auth_service import AuthService
from app.models.user import User


class TestAuthService:
    """认证服务测试"""
    
    @pytest.mark.asyncio
    async def test_send_verification_code(self, db_session):
        """测试发送验证码"""
        service = AuthService(db_session)
        result = await service.send_verification_code("13800138000")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_login_with_invalid_code(self, db_session):
        """测试无效验证码登录"""
        service = AuthService(db_session)
        result = await service.login("13800138000", "123456")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_or_create_user(self, db_session):
        """测试获取或创建用户"""
        service = AuthService(db_session)
        user = await service._get_or_create_user("13800138000")
        
        assert user is not None
        assert user.phone == "13800138000"
        assert user.level == "入门"
        assert user.total_score == 0
    
    @pytest.mark.asyncio
    async def test_ensure_subscription(self, db_session):
        """测试确保订阅"""
        service = AuthService(db_session)
        user = await service._get_or_create_user("13800138000")
        subscription = await service._ensure_subscription(user.id)
        
        assert subscription is not None
        assert subscription.user_id == user.id
        assert subscription.token_quota > 0
