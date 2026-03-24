"""路由 Agent - 意图识别和分发"""
from typing import Dict, Any
from app.agents.base import BaseAgent


class RouterAgent(BaseAgent):
    """路由 Agent - 识别用户意图并分发到对应 Agent"""
    
    def __init__(self):
        super().__init__(
            name="router",
            description="意图识别和路由分发"
        )
        self.intent_keywords = {
            "goal_discussion": ["想学", "目标", "学习", "计划", "课程"],
            "plan_adjust": ["调整", "改", "不满意", "太难", "太简单"],
            "feedback": ["完成", "打卡", "学会了", "反馈", "怎么样"]
        }
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        识别意图并路由
        
        1. 分析用户消息
        2. 判断意图类型
        3. 返回目标 Agent
        """
        message = context.get("message", "")
        session_type = context.get("session_type", "goal_discussion")
        
        # 简单基于关键词的意图识别
        intent = self._classify_intent(message)
        
        self.log("info", f"意图识别: {intent}, message: {message[:30]}...")
        
        return {
            "intent": intent,
            "session_type": intent,  # 更新会话类型
            "metadata": {
                "confidence": 0.8,  # TODO: 计算置信度
                "keywords": self._extract_keywords(message)
            }
        }
    
    def _classify_intent(self, message: str) -> str:
        """基于关键词分类"""
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return intent
        return "goal_discussion"  # 默认意图
    
    def _extract_keywords(self, message: str) -> list:
        """提取关键词"""
        keywords = []
        for intent, intent_keywords in self.intent_keywords.items():
            for keyword in intent_keywords:
                if keyword in message:
                    keywords.append(keyword)
        return list(set(keywords))
