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
        self.router = RouterAgent()
        self.agents = {
            "goal_discussion": GoalAgent(),
            "plan_adjust": GoalAgent(),  # 复用目标Agent，调整对话逻辑
            "feedback": FeedbackAgent()
        }
        self.default_agent = GoalAgent()
    
    async def route(
        self,
        user_id: str,
        message: str,
        session_id: str,
        session_type: str = "goal_discussion"
    ) -> Dict[str, Any]:
        """
        路由消息到对应 Agent
        
        1. 调用路由 Agent 识别意图
        2. 根据意图分发到对应 Agent
        3. 返回 Agent 响应
        """
        logger.info(f"路由消息: user={user_id}, type={session_type}")
        
        # 构建上下文
        context = {
            "user_id": user_id,
            "message": message,
            "session_id": session_id,
            "session_type": session_type
        }
        
        # 意图识别（简化版，直接使用 session_type）
        # TODO: 集成 RouterAgent 进行智能识别
        intent = session_type
        
        # 分发到对应 Agent
        agent = self.agents.get(intent, self.default_agent)
        
        logger.info(f"分发到 Agent: {agent.name}")
        
        # 处理请求
        result = await agent.process(context)
        
        return result
