"""Agent 路由器"""
from typing import Dict, Any
from app.agents.router_agent import RouterAgent
from app.agents.goal_agent import GoalAgent
from app.agents.plan_agent import PlanAgent
from app.agents.feedback_agent import FeedbackAgent
from app.core.logging import get_logger

logger = get_logger("agents.router")


class AgentRouter:
    """Agent 路由 - 根据意图分发到对应 Agent"""
    
    def __init__(self):
        self.router_agent = RouterAgent()
        self.goal_agent = GoalAgent()
        self.plan_agent = PlanAgent()
        self.feedback_agent = FeedbackAgent()
        
        # Agent 映射
        self.agents = {
            "goal_discussion": self.goal_agent,
            "plan_adjust": self.goal_agent,
            "feedback": self.feedback_agent,
            "plan_generate": self.plan_agent
        }
        
        # 默认 Agent
        self.default_agent = self.goal_agent
    
    async def route(
        self,
        user_id: str,
        message: str,
        session_id: str,
        session_type: str = "goal_discussion",
        context: Dict[str, Any] = None,
        history: list = None
    ) -> Dict[str, Any]:
        """
        路由消息到对应 Agent
        
        1. 解析会话类型和上下文
        2. 根据上下文判断是否需要生成计划
        3. 分发到对应 Agent
        4. 返回 Agent 响应
        """
        logger.info(f"路由消息: user={user_id}, type={session_type}")
        
        # 合并上下文
        full_context = context or {}
        full_context.update({
            "user_id": user_id,
            "message": message,
            "session_id": session_id,
            "session_type": session_type,
            "history": history or []
        })
        
        # 检查是否准备生成计划
        collected_info = full_context.get("collected_info", {})
        
        # 如果收集到足够信息，自动触发计划生成
        if session_type == "goal_discussion":
            required_fields = ["subject", "target", "daily_duration"]
            missing = [f for f in required_fields if not collected_info.get(f)]
            
            # 如果没有缺失字段，询问是否生成计划
            if not missing:
                # 检查用户是否确认
                confirm_keywords = ["确认", "好", "可以", "开始", "生成", "执行"]
                if any(kw in message for kw in confirm_keywords):
                    full_context["collected_info"] = collected_info
                    logger.info("触发计划生成 Agent")
                    return await self.plan_agent.process(full_context)
        
        # 根据 session_type 选择 Agent
        agent = self.agents.get(session_type, self.default_agent)
        
        logger.info(f"分发到 Agent: {agent.name}")
        
        # 处理请求
        try:
            result = await agent.process(full_context)
            
            # 如果 Agent 返回准备生成计划，且用户确认了
            if result.get("metadata", {}).get("ready_for_plan"):
                confirm_keywords = ["确认", "好", "可以", "开始", "生成"]
                if any(kw in message for kw in confirm_keywords):
                    result = await self.plan_agent.process(full_context)
            
            return result
            
        except Exception as e:
            logger.error(f"Agent 处理失败: {str(e)}")
            return {
                "content": "抱歉，处理你的请求时遇到问题，请稍后重试。",
                "token_used": 0,
                "metadata": {}
            }
