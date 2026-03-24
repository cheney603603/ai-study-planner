"""
测试：Agent 路由器
覆盖：字段统一化、确认关键词识别、降级响应
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAgentRouterNormalize:
    """_normalize 方法：统一 response 字段"""

    def test_response_key_unchanged(self):
        from app.agents.agent_router import AgentRouter
        result = {"response": "hello", "token_used": 10}
        normalized = AgentRouter._normalize(result)
        assert normalized["response"] == "hello"

    def test_content_key_renamed_to_response(self):
        from app.agents.agent_router import AgentRouter
        result = {"content": "fallback msg", "token_used": 0}
        normalized = AgentRouter._normalize(result)
        assert normalized["response"] == "fallback msg"
        assert "content" not in normalized

    def test_empty_dict_gets_empty_response(self):
        from app.agents.agent_router import AgentRouter
        result = {}
        normalized = AgentRouter._normalize(result)
        assert normalized["response"] == ""


class TestAgentRouterConfirm:
    """确认关键词识别"""

    def test_confirm_keywords(self):
        from app.agents.agent_router import AgentRouter
        router = AgentRouter.__new__(AgentRouter)
        assert router._is_confirm("好的，开始吧") is True
        assert router._is_confirm("可以，生成计划") is True
        assert router._is_confirm("确认") is True

    def test_non_confirm_message(self):
        from app.agents.agent_router import AgentRouter
        router = AgentRouter.__new__(AgentRouter)
        assert router._is_confirm("我想学 Python") is False
        assert router._is_confirm("每天学 2 小时") is False
