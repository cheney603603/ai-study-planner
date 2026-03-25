"""Agent 路由器"""
import threading
from typing import Dict, Any, TYPE_CHECKING

from app.core.logging import get_logger

logger = get_logger("agents.router")

# 确认意图关键词
_CONFIRM_KEYWORDS = ["确认", "好的", "可以", "开始", "生成", "执行", "没问题", "就这样"]

# Agent 惰性初始化（线程安全单例）
_router_lock = threading.Lock()
_initialized = False


def _get_router() -> "AgentRouter":
    """获取或创建 AgentRouter（线程安全）"""
    global _initialized
    if _initialized:
        return AgentRouter

    with _router_lock:
        if not _initialized:
            AgentRouter._setup_agents()
            _initialized = True
            logger.info("AgentRouter 初始化完成（线程安全单例）")
        return AgentRouter


class AgentRouter:
    """
    Agent 路由 - 根据意图分发到对应 Agent

    所有 Agent 在首次访问时惰性初始化，后续复用。
    """

    _goal_agent = None
    _plan_agent = None
    _feedback_agent = None

    agents: Dict[str, Any] = {}
    default_agent: Any = None

    @classmethod
    def _setup_agents(cls):
        """初始化所有 Agent（仅调用一次）"""
        from app.agents.goal_agent import GoalAgent
        from app.agents.plan_agent import PlanAgent
        from app.agents.feedback_agent import FeedbackAgent

        cls._goal_agent = GoalAgent()
        cls._plan_agent = PlanAgent()
        cls._feedback_agent = FeedbackAgent()

        cls.agents = {
            "goal_discussion": cls._goal_agent,
            "plan_adjust": cls._goal_agent,
            "feedback": cls._feedback_agent,
            "plan_generate": cls._plan_agent,
        }
        cls.default_agent = cls._goal_agent

    @staticmethod
    def _is_confirm(message: str) -> bool:
        return any(kw in message for kw in _CONFIRM_KEYWORDS)

    async def route(
        self,
        user_id: str,
        message: str,
        session_id: str,
        session_type: str = "goal_discussion",
        context: Dict[str, Any] = None,
        history: list = None,
    ) -> Dict[str, Any]:
        """路由消息到对应 Agent，统一返回 response 字段"""
        logger.info(f"路由消息: user={user_id}, type={session_type}")

        full_context = context or {}
        full_context.update(
            {
                "user_id": user_id,
                "message": message,
                "session_id": session_id,
                "session_type": session_type,
                "history": history or [],
            }
        )

        collected_info = full_context.get("collected_info", {})

        # 信息充分 + 用户确认 → 直接生成计划
        if session_type == "goal_discussion":
            required_fields = ["subject", "target", "daily_duration"]
            missing = [f for f in required_fields if not collected_info.get(f)]
            if not missing and self._is_confirm(message):
                full_context["collected_info"] = collected_info
                logger.info("触发计划生成 Agent")
                result = await self._plan_agent.process(full_context)
                return self._normalize(result)

        agent = self.agents.get(session_type, self.default_agent)
        logger.info(f"分发到 Agent: {agent.name}")

        try:
            result = await agent.process(full_context)

            if result.get("metadata", {}).get("ready_for_plan") and self._is_confirm(message):
                result = await self._plan_agent.process(full_context)

            return self._normalize(result)

        except Exception as e:
            logger.error(f"Agent 处理失败: {str(e)}", exc_info=True)
            return {
                "response": "抱歉，处理你的请求时遇到问题，请稍后重试。",
                "token_used": 0,
                "metadata": {},
            }

    @staticmethod
    def _normalize(result: Dict[str, Any]) -> Dict[str, Any]:
        """统一响应字段：确保始终有 response 键"""
        if "response" not in result:
            result["response"] = result.pop("content", "")
        return result


# 快捷调用（内部使用）
def get_agent_router() -> AgentRouter:
    """获取 AgentRouter 实例"""
    return _get_router()
