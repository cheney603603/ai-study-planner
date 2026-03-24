"""徽章引擎单元测试"""
import pytest
from app.services.badge_engine import BadgeEngine, LEVELS


class TestBadgeEngine:
    """徽章引擎测试"""
    
    @pytest.mark.asyncio
    async def test_calculate_level(self):
        """测试等级计算"""
        engine = BadgeEngine(None)
        
        assert engine.calculate_level(0) == "入门"
        assert engine.calculate_level(100) == "入门"
        assert engine.calculate_level(500) == "进阶"
        assert engine.calculate_level(1000) == "进阶"
        assert engine.calculate_level(2000) == "大师"
        assert engine.calculate_level(5000) == "宗师"
    
    def test_levels_definition(self):
        """测试等级定义"""
        assert len(LEVELS) == 4
        assert LEVELS[0]["name"] == "入门"
        assert LEVELS[1]["name"] == "进阶"
        assert LEVELS[2]["name"] == "大师"
        assert LEVELS[3]["name"] == "宗师"
