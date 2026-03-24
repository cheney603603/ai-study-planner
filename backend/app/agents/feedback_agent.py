"""评估反馈 Agent"""
from typing import Dict, Any
from app.agents.base import BaseAgent


class FeedbackAgent(BaseAgent):
    """评估反馈 Agent - 分析完成情况，提供鼓励和建议"""
    
    def __init__(self):
        super().__init__(
            name="feedback_agent",
            description="评估学习反馈，提供鼓励和建议"
        )
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理反馈
        
        1. 分析任务完成情况
        2. 生成鼓励话语
        3. 提供下步建议
        """
        message = context.get("message", "")
        task_result = context.get("task_result", {})
        streak_info = context.get("streak_info", {})
        
        # 分析反馈类型
        feedback_type = self._classify_feedback(message)
        
        # 生成响应
        response = self._generate_feedback(feedback_type, task_result, streak_info)
        
        self.log("info", f"反馈生成: type={feedback_type}")
        
        return {
            "response": response,
            "token_used": 80,
            "metadata": {
                "feedback_type": feedback_type,
                "encouragement_level": "high"
            }
        }
    
    def _classify_feedback(self, message: str) -> str:
        """分类反馈"""
        positive_keywords = ["完成", "学会了", "懂了", "掌握了", "好"]
        negative_keywords = ["不懂", "难", "不会", "困惑", "卡住了"]
        neutral_keywords = ["继续", "下一步", "下一个"]
        
        for kw in positive_keywords:
            if kw in message:
                return "positive"
        for kw in negative_keywords:
            if kw in message:
                return "negative"
        return "neutral"
    
    def _generate_feedback(
        self,
        feedback_type: str,
        task_result: dict,
        streak_info: dict
    ) -> str:
        """生成反馈"""
        responses = {
            "positive": (
                "🎉 太棒了！你已经完成了今天的任务！\n\n"
                "继续保持这个节奏，你一定能达成目标！\n\n"
                "📈 当前连续学习：{streak} 天\n"
                "💎 获得积分：+{score}\n\n"
                "继续加油，明天见！"
            ),
            "negative": (
                "🤔 学习过程中遇到困难是很正常的！\n\n"
                "不要气馁，可以试试：\n"
                "1. 回顾一下之前的知识点\n"
                "2. 把问题分解成小块\n"
                "3. 搜索相关资料\n\n"
                "需要我帮你解释一下吗？"
            ),
            "neutral": (
                "📖 好的，让我们继续！\n\n"
                "今日任务：\n"
                "1. 复习昨天的内容\n"
                "2. 学习新知识点\n"
                "3. 完成练习题\n\n"
                "开始吧！"
            )
        }
        
        response = responses.get(feedback_type, responses["neutral"])
        
        # 填充数据
        streak = streak_info.get("current_streak", 1)
        score = task_result.get("score", 10)
        
        return response.format(streak=streak, score=score)
