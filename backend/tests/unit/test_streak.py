"""
测试：连续学习天数计算
覆盖：连续/中断/空数据 等场景
"""
import pytest
from datetime import datetime, timedelta, date
from unittest.mock import AsyncMock, MagicMock, patch


# ------------------------------------------------------------------ #
# 纯函数：连续天数计算（从 plan_service 提取逻辑，便于单元测试）
# ------------------------------------------------------------------ #

def calculate_streak_from_dates(completed_dates: list[date]) -> int:
    """
    从已完成日期列表计算连续天数（纯函数，便于测试）
    """
    if not completed_dates:
        return 0

    sorted_dates = sorted(set(completed_dates), reverse=True)
    today = datetime.utcnow().date()
    streak = 0
    expected = today

    for d in sorted_dates:
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)
        elif d < expected:
            break

    return streak


# ------------------------------------------------------------------ #
# 测试用例
# ------------------------------------------------------------------ #

class TestStreakCalculation:

    def test_empty_returns_zero(self):
        assert calculate_streak_from_dates([]) == 0

    def test_only_today(self):
        today = datetime.utcnow().date()
        assert calculate_streak_from_dates([today]) == 1

    def test_consecutive_3_days(self):
        today = datetime.utcnow().date()
        dates = [today - timedelta(days=i) for i in range(3)]
        assert calculate_streak_from_dates(dates) == 3

    def test_consecutive_7_days(self):
        today = datetime.utcnow().date()
        dates = [today - timedelta(days=i) for i in range(7)]
        assert calculate_streak_from_dates(dates) == 7

    def test_gap_breaks_streak(self):
        """中间有一天没打卡，连续天数应该中断"""
        today = datetime.utcnow().date()
        # 今天 + 前天（跳过昨天）
        dates = [today, today - timedelta(days=2)]
        assert calculate_streak_from_dates(dates) == 1

    def test_only_yesterday(self):
        """只有昨天打卡，今天没打，连续天数为 0"""
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        assert calculate_streak_from_dates([yesterday]) == 0

    def test_duplicate_dates_counted_once(self):
        """同一天多次打卡只算一次"""
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        dates = [today, today, yesterday, yesterday]
        assert calculate_streak_from_dates(dates) == 2

    def test_long_streak_with_gap(self):
        """长连续后有中断，只计算最近连续段"""
        today = datetime.utcnow().date()
        # 今天 + 昨天 = 2 天连续，然后 5 天前有记录（中断）
        dates = [today, today - timedelta(days=1), today - timedelta(days=5)]
        assert calculate_streak_from_dates(dates) == 2
