"""学习目标理解 Agent"""
from typing import Dict, Any, List
from app.agents.base import BaseAgent

# 系统提示词
SYSTEM_PROMPT = """你是一位专业的学习规划顾问，擅长通过对话了解用户的学习需求。

你的任务是：
1. 通过友好的对话，了解用户想学什么
2. 收集关键信息：学习主题、学习目标、每日可用时间、期望完成时间
3. 当信息充分时，总结确认用户需求

回复要求：
- 保持对话简洁，每次只问 1-2 个问题
- 使用友好的语气，像朋友聊天一样
- 当收集到足够信息时，生成需求摘要
- 用中文回复

收集的信息包括：
- subject: 学习主题（如 Python、 英语、机器学习等）
- target: 学习目标（想达到什么程度）
- daily_duration: 每日可用时间（分钟）
- deadline: 期望完成时间
- knowledge_level: 当前知识水平（入门/进阶）
"""


class GoalAgent(BaseAgent):
    """学习目标理解 Agent - 引导用户明确学习需求"""
    
    def __init__(self):
        super().__init__(
            name="goal_agent",
            description="理解用户学习目标，收集关键信息"
        )
        self.required_fields = ["subject", "target", "daily_duration"]
    
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
        
        # 构建对话历史（用于 LLM 理解上下文）
        history_text = ""
        if history:
            for h in history[-5:]:  # 只取最近5条
                role = "用户" if h.get("role") == "user" else "AI"
                history_text += f"{role}: {h.get('content', '')[:100]}\n"
        
        # 构建提示词
        prompt = f"""之前的对话摘要：
{history_text}

当前收集到的信息：
{self._format_collected_info(collected_info)}

用户最新输入：{message}

请根据用户的输入，判断：
1. 能否提取到新的信息？
2. 是否还需要更多问题？
3. 如果信息充分，请生成需求摘要

直接回复用户，不需要解释你的思考过程。"""
        
        # 调用 LLM
        llm_result = await self._call_llm(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.8
        )
        
        response_text = llm_result.get("response", "")
        token_used = llm_result.get("token_used", 0)
        
        # 尝试从回复中提取信息
        new_info = self._extract_info_from_text(response_text + message)
        collected_info.update(new_info)
        
        # 检查是否准备生成计划
        missing_fields = [f for f in self.required_fields if f not in collected_info or not collected_info[f]]
        
        self.log("info", f"目标理解: 已收集 {len(collected_info)} 项信息, 缺失: {missing_fields}")
        
        return {
            "response": response_text,
            "token_used": token_used,
            "metadata": {
                "collected_info": collected_info,
                "missing_fields": missing_fields,
                "ready_for_plan": len(missing_fields) == 0
            }
        }
    
    def _format_collected_info(self, info: dict) -> str:
        """格式化已收集的信息"""
        if not info:
            return "暂无收集到信息"
        
        lines = []
        if info.get("subject"):
            lines.append(f"- 学习主题: {info['subject']}")
        if info.get("target"):
            lines.append(f"- 学习目标: {info['target']}")
        if info.get("daily_duration"):
            lines.append(f"- 每日时间: {info['daily_duration']} 分钟")
        if info.get("deadline"):
            lines.append(f"- 完成时间: {info['deadline']}")
        if info.get("knowledge_level"):
            lines.append(f"- 当前水平: {info['knowledge_level']}")
        
        return "\n".join(lines) if lines else "暂无收集到信息"
    
    def _extract_info_from_text(self, text: str) -> dict:
        """从文本中提取结构化信息"""
        info = {}
        text_lower = text.lower()
        
        # 提取时间
        import re
        
        # 匹配 "每天X小时" 或 "每天X分钟"
        time_patterns = [
            r'每天(\d+)\s*小时',
            r'每天(\d+)\s*分钟',
            r'每天(\d+)\s*h',
            r'每天(\d+)\s*m',
            r'每天(\d+)小时',
            r'每天(\d+)分钟',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                value = int(match.group(1))
                if '小时' in pattern or 'h' in pattern.lower():
                    value = value * 60
                info['daily_duration'] = value
                break
        
        # 提取主题（常见关键词）
        subjects = ['python', 'python编程', '英语', '日语', '法语', '机器学习', '深度学习',
                    '数据分析', '前端', '后端', 'java', 'javascript', 'c++', 'go',
                    '公务员', '考研', '托福', '雅思', '钢琴', '吉他', '绘画', '摄影']
        
        for subject in subjects:
            if subject in text_lower:
                info['subject'] = subject
                break
        
        # 提取知识水平
        if '零基础' in text or '完全不会' in text or '新手' in text:
            info['knowledge_level'] = '入门'
        elif '基础' in text or '会一点' in text:
            info['knowledge_level'] = '进阶'
        
        return info
