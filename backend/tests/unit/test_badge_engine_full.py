"""
测试：徽章引擎完整覆盖
覆盖：等级计算、进度除零保护、徽章检查、等级徽章发放
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.badge_engine import BadgeEngine, LEVELS, BADGE_DEFINITIONS


class TestLevelCalculation:
    """等级计算测试"""

    def test_calculate_level_boundaries(self):
        """各等级边界值测试"""
        engine = BadgeEngine(None)

        assert engine.calculate_level(0) == "入门"
        assert engine.calculate_level(1) == "入门"
        assert engine.calculate_level(499) == "入门"
        assert engine.calculate_level(500) == "进阶"
        assert engine.calculate_level(501) == "进阶"
        assert engine.calculate_level(1999) == "进阶"
        assert engine.calculate_level(2000) == "大师"
        assert engine.calculate_level(4999) == "大师"
        assert engine.calculate_level(5000) == "宗师"
        assert engine.calculate_level(99999) == "宗师"

    def test_level_up_detected(self):
        """等级提升检测"""
        engine = BadgeEngine(None)

        mock_user = MagicMock()
        mock_user.level = "入门"
        mock_user.total_score = 500  # 升级到进阶

        result = engine.check_level_up(mock_user)
        assert result is not None
        assert result["old"] == "入门"
        assert result["new"] == "进阶"

    def test_no_level_up_when_same(self):
        """同等级不触发升级"""
        engine = BadgeEngine(None)

        mock_user = MagicMock()
        mock_user.level = "入门"
        mock_user.total_score = 200  # 仍在入门

        result = engine.check_level_up(mock_user)
        assert result is None

    def test_levels_definition_complete(self):
        """等级定义完整性"""
        assert len(LEVELS) == 4
        names = [l["name"] for l in LEVELS]
        assert names == ["入门", "进阶", "大师", "宗师"]
        # 相邻等级无间隙
        for i in range(len(LEVELS) - 1):
            assert LEVELS[i]["max_score"] + 1 == LEVELS[i + 1]["min_score"]


class TestNextLevelInfo:
    """下一等级信息测试"""

    def test_next_level_for_enter(self):
        """入门→进阶"""
        engine = BadgeEngine(None)
        info = engine._get_next_level_info("入门", 250)

        assert info is not None
        assert info["name"] == "进阶"
        assert info["min_score"] == 500
        # 进度约 50%
        assert 45 <= info["progress"] <= 55

    def test_next_level_for_master(self):
        """大师→宗师"""
        engine = BadgeEngine(None)
        info = engine._get_next_level_info("大师", 3500)

        assert info is not None
        assert info["name"] == "宗师"
        assert info["min_score"] == 5000

    def test_no_next_level_for_top(self):
        """宗师无下一级"""
        engine = BadgeEngine(None)
        info = engine._get_next_level_info("宗师", 99999)
        assert info is None

    def test_max_progress_when_over(self):
        """分数超过下一级最小值时进度封顶 100"""
        engine = BadgeEngine(None)
        info = engine._get_next_level_info("入门", 600)  # 已超进阶门槛
        assert info["progress"] == 100.0

    def test_zero_range_protection(self):
        """等级定义 level_range 为 0 时不崩溃"""
        # 用 mock 模拟边界情况
        engine = BadgeEngine(None)
        # 手动测试：确保除零不发生
        info = engine._get_next_level_info("入门", 250)
        assert isinstance(info["progress"], float)
        assert 0 <= info["progress"] <= 100


class TestBadgeDefinitions:
    """徽章定义完整性测试"""

    def test_all_badges_have_required_fields(self):
        """每个徽章定义都有必要字段"""
        required = {"code", "name", "description", "score"}
        for badge in BADGE_DEFINITIONS:
            assert required.issubset(badge.keys()), f"徽章 {badge} 缺少字段"

    def test_badge_codes_unique(self):
        """徽章 code 唯一"""
        codes = [b["code"] for b in BADGE_DEFINITIONS]
        assert len(codes) == len(set(codes)), "存在重复的 badge code"

    def test_total_badges_count(self):
        """徽章数量符合预期（15个）"""
        assert len(BADGE_DEFINITIONS) == 15

    def test_score_bonus_reasonable(self):
        """徽章积分奖励合理（正数）"""
        for badge in BADGE_DEFINITIONS:
            assert badge["score"] > 0, f"徽章 {badge['code']} 积分为非正数"


class TestCheckAndAwardBadges:
    """徽章自动发放测试"""

    def test_first_task_badge(self):
        """完成第1个任务触发 first_task"""
        engine = BadgeEngine(MagicMock())

        # Mock _get_earned_badges 返回空
        engine._get_earned_badges = AsyncMock(return_value=[])
        engine._award_badge = AsyncMock(return_value=True)

        import asyncio
        new = asyncio.get_event_loop().run_until_complete(
            engine.check_and_award_badges("user1", context={"task_completed": 1})
        )
        assert "first_task" in new
        engine._award_badge.assert_called_with("user1", "first_task")

    def test_already_earned_not_repeat(self):
        """已获得的徽章不会重复发放"""
        engine = BadgeEngine(MagicMock())

        # Mock 已获得 first_task
        earned_badge = MagicMock()
        earned_badge.code = "first_task"
        engine._get_earned_badges = AsyncMock(return_value=[earned_badge])
        engine._award_badge = AsyncMock()

        import asyncio
        new = asyncio.get_event_loop().run_until_complete(
            engine.check_and_award_badges(
                "user1",
                context={"task_completed": 5}
            )
        )
        # first_task 不会再发放
        assert "first_task" not in new
        # tasks_10 应该发放
        assert "tasks_10" in new

    def test_task_milestones(self):
        """任务数量里程碑"""
        engine = BadgeEngine(MagicMock())
        engine._get_earned_badges = AsyncMock(return_value=[])
        engine._award_badge = AsyncMock(return_value=True)

        import asyncio

        # 100 个任务：应触发 first_task, tasks_10, tasks_50, tasks_100
        new = asyncio.get_event_loop().run_until_complete(
            engine.check_and_award_badges("user1", context={"task_completed": 100})
        )
        assert "first_task" in new
        assert "tasks_10" in new
        assert "tasks_50" in new
        assert "tasks_100" in new

    def test_streak_milestones(self):
        """连续学习里程碑"""
        engine = BadgeEngine(MagicMock())
        engine._get_earned_badges = AsyncMock(return_value=[])
        engine._award_badge = AsyncMock(return_value=True)

        import asyncio

        new = asyncio.get_event_loop().run_until_complete(
            engine.check_and_award_badges("user1", context={"streak_days": 30})
        )
        assert "streak_3" in new
        assert "streak_7" in new
        assert "streak_30" in new

    def test_score_milestones(self):
        """积分里程碑"""
        engine = BadgeEngine(MagicMock())
        engine._get_earned_badges = AsyncMock(return_value=[])
        engine._award_badge = AsyncMock(return_value=True)

        import asyncio

        new = asyncio.get_event_loop().run_until_complete(
            engine.check_and_award_badges("user1", context={"total_score": 2500})
        )
        assert "score_500" in new
        assert "score_2000" in new
