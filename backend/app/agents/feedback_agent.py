"""评估反馈 Agent"""
from typing import Dict, Any
from app.agents.base import BaseAgent

# 系统提示词
SYSTEM_PROMPT = """你是一位温暖的学习导师，擅长鼓励学习者、给出反馈和建议。

你的职责：
1. 对用户完成的任务给予真诚的鼓励和肯定
2. 分析学习情况，给出适当的建议
3. 帮助用户保持学习动力

回复要求：
- 保持温暖、鼓励的语气
- 简短有力，不要太长
- 适时给予小技巧或建议
- 用中文回复
"""


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
        history = context.get("history", [])
        
        # 构建上下文
        streak = streak_info.get("current_streak", 0)
        score = task_result.get("score", 0)
        total_score = task_result.get("total_score", 0)
        level = task_result.get("level", "入门")
        
        # 构建历史摘要
        history_summary = ""
        if history:
            recent = history[-3:]
            for h in recent:
                role = "你" if h.get("role") == "user" else "我"
                history_summary += f"{role}: {h.get('content', '')[:50]}...\n"
        
        # 构建提示词
        prompt = f"""学习情况摘要：
- 当前连续学习：{streak} 天
- 本次获得积分：+{score}
- 总积分：{total_score}
- 当前等级：{level}

最近的对话：
{history_summary}

用户说：{message}

请给予温暖的鼓励和适当的建议。简短有力，30-50字左右。"""
        
        # 调用 LLM
        llm_result = await self._call_llm(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.9
        )
        
        response = llm_result.get("response", "")
        token_used = llm_result.get("token_used", 0)
        
        # 添加额外的激励信息
        extra_info = ""
        if streak >= 7:
            extra_info = "\n\n🔥 连续学习 7 天了！继续保持！"
        elif streak >= 3:
            extra_info = "\n\n💪 学习习惯正在养成！"
        
        response += extra_info
        
        self.log("info", f"反馈生成: streak={streak}, score={score}")
        
        return {
            "response": response,
            "token_used": token_used,
            "metadata": {
                "encouragement_level": "high" if streak >= 7 else "normal",
                "streak": streak,
                "score": score
            }
        }
