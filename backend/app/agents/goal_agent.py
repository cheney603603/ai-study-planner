"""学习目标理解 Agent"""
from typing import Dict, Any, List
from app.agents.base import BaseAgent


class GoalAgent(BaseAgent):
    """学习目标理解 Agent - 引导用户明确学习需求"""
    
    def __init__(self):
        super().__init__(
            name="goal_agent",
            description="理解用户学习目标，收集关键信息"
        )
        self.required_info = [
            "subject",      # 学习主题
            "target",       # 学习目标
            "duration",     # 每日可用时间
            "deadline"      # 期望完成时间
        ]
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理学习目标对话
        
        1. 分析用户消息
        2. 提取/更新学习信息
        3. 判断信息是否充分
        4. 生成引导回复
        """
        message = context.get("message", "")
        collected_info = context.get("collected_info", {})
        history = context.get("history", [])
        
        # 分析消息，提取信息
        new_info = self._extract_info(message, collected_info)
        collected_info.update(new_info)
        
        # 检查是否需要更多信息
        missing_info = self._get_missing_info(collected_info)
        
        # 生成回复
        if missing_info:
            response = self._generate_guidance(missing_info, collected_info)
        else:
            response = self._generate_confirmation(collected_info)
        
        self.log("info", f"目标理解: 已收集 {len(collected_info)} 项信息")
        
        return {
            "response": response,
            "token_used": 150,
            "metadata": {
                "collected_info": collected_info,
                "missing_info": missing_info,
                "ready_for_plan": len(missing_info) == 0
            }
        }
    
    def _extract_info(self, message: str, current: dict) -> dict:
        """从消息中提取信息"""
        info = {}
        
        # TODO: 使用 LLM 或正则提取更准确的信息
        # 当前简化实现
        
        if "想学" in message or "学习" in message:
            # 提取学习主题
            info["subject"] = message
        
        if "小时" in message or "分钟" in message:
            # 提取时间
            if "小时" in message:
                info["daily_duration"] = int(message.split("小时")[0].split()[-1]) * 60
            else:
                info["daily_duration"] = int(message.split("分钟")[0].split()[-1])
        
        return info
    
    def _get_missing_info(self, collected: dict) -> List[str]:
        """获取缺失的信息"""
        missing = []
        for key in self.required_info:
            if key not in collected:
                missing.append(key)
        return missing
    
    def _generate_guidance(self, missing: List[str], current: dict) -> str:
        """生成引导回复"""
        responses = {
            "subject": "好的！请告诉我你想学习什么主题？比如：Python 编程、英语、机器学习等。",
            "target": "你的学习目标是什么？比如：找到一份相关工作、通过某个考试、掌握某个技能等。",
            "duration": "你每天大概有多少时间可以用于学习？比如：每天1小时、每天30分钟等。",
            "deadline": "你希望什么时候完成学习目标？有没有截止日期？"
        }
        
        # 返回第一个缺失项的引导
        if missing:
            return responses.get(missing[0], "请告诉我更多信息。")
        
        return "好的，请继续补充信息。"
    
    def _generate_confirmation(self, info: dict) -> str:
        """生成确认信息"""
        return (
            f"好的！我已经了解了你的学习需求：\n\n"
            f"📚 学习主题：{info.get('subject', '待定')}\n"
            f"🎯 学习目标：{info.get('target', '待定')}\n"
            f"⏰ 每日时间：{info.get('daily_duration', 60)} 分钟\n"
            f"📅 完成时间：{info.get('deadline', '待定')}\n\n"
            f"确认无误后，我将为你生成详细的学习计划！"
        )
