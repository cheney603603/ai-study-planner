"""计划生成 Agent"""
import json
from typing import Dict, Any
from app.agents.base import BaseAgent

# 系统提示词
SYSTEM_PROMPT = """你是一位专业的学习规划师，擅长根据用户需求制定详细的学习计划。

你的职责：
1. 根据收集到的学习信息，生成个性化学习计划
2. 计划必须包含：阶段划分、每日任务、里程碑
3. 确保计划可执行、可量化、可追踪

输出要求：
- 使用 JSON 格式输出计划
- 计划应该平衡挑战性和可达性
- 考虑用户的生活习惯和可用时间

JSON 格式：
{
    "title": "计划标题",
    "subject": "学习主题",
    "target": "学习目标",
    "total_days": 总天数,
    "daily_duration": 每日分钟数,
    "phases": [
        {
            "name": "阶段名称",
            "duration_days": 天数,
            "description": "阶段描述",
            "goals": ["目标1", "目标2"],
            "daily_tasks_avg": 日均任务数
        }
    ],
    "milestones": [
        {"day": 第几天, "description": "里程碑描述"}
    ]
}
"""


class PlanAgent(BaseAgent):
    """计划生成 Agent - 生成个性化学习计划"""
    
    def __init__(self):
        super().__init__(
            name="plan_agent",
            description="生成个性化学习计划"
        )
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成学习计划
        
        1. 汇总收集的信息
        2. 调用 LLM 生成计划
        3. 格式化输出
        """
        collected_info = context.get("collected_info", {})
        session_id = context.get("session_id")
        
        self.log("info", f"开始生成计划: session={session_id}")
        
        # 构建提示词
        prompt = self._build_prompt(collected_info)
        
        # 调用 LLM
        llm_result = await self._call_llm(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7
        )
        
        response_text = llm_result.get("response", "")
        token_used = llm_result.get("token_used", 0)
        
        # 解析计划
        plan = self._parse_plan(response_text, collected_info)
        
        # 格式化响应
        response = self._format_plan_response(plan)
        
        self.log("info", f"计划生成完成: {len(plan.get('phases', []))} 个阶段")
        
        return {
            "response": response,
            "token_used": token_used,
            "metadata": {
                "plan": plan,
                "ready_to_save": True
            }
        }
    
    def _build_prompt(self, info: dict) -> str:
        """构建 LLM 提示词"""
        return f"""请为以下学习需求生成一个详细的学习计划：

学习主题：{info.get('subject', '待定')}
学习目标：{info.get('target', '待定')}
每日可用时间：{info.get('daily_duration', 60)} 分钟
期望完成时间：{info.get('deadline', '待定')}
当前知识水平：{info.get('knowledge_level', '入门')}

请生成一个平衡的学习计划，包含阶段划分和里程碑。用 JSON 格式返回。"""
    
    def _parse_plan(self, llm_response: str, info: dict) -> dict:
        """解析 LLM 返回的计划"""
        try:
            # 尝试提取 JSON
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                plan = json.loads(json_str)
                return plan
        except json.JSONDecodeError:
            self.log("warning", "JSON 解析失败，使用默认格式")
        
        # Fallback：生成默认计划
        return self._generate_default_plan(info)
    
    def _generate_default_plan(self, info: dict) -> dict:
        """生成默认计划（当 LLM 返回格式错误时）"""
        total_days = 30  # 默认一个月
        
        return {
            "title": f"{info.get('subject', '学习')}学习计划",
            "subject": info.get("subject", "通用学习"),
            "target": info.get("target", "掌握相关知识"),
            "total_days": total_days,
            "daily_duration": info.get("daily_duration", 60),
            "phases": [
                {
                    "name": "第一阶段：基础入门",
                    "duration_days": 10,
                    "description": "了解基本概念和核心知识点",
                    "goals": ["掌握基础概念", "能够进行简单应用"],
                    "daily_tasks_avg": 2
                },
                {
                    "name": "第二阶段：进阶提升",
                    "duration_days": 12,
                    "description": "深入理解原理，进行实践练习",
                    "goals": ["理解核心原理", "能够独立完成练习"],
                    "daily_tasks_avg": 3
                },
                {
                    "name": "第三阶段：实战巩固",
                    "duration_days": 8,
                    "description": "完成项目实战，总结复盘",
                    "goals": ["完成综合项目", "形成知识体系"],
                    "daily_tasks_avg": 2
                }
            ],
            "milestones": [
                {"day": 10, "description": "完成基础阶段"},
                {"day": 22, "description": "完成进阶阶段"},
                {"day": 30, "description": "完成全部学习"}
            ]
        }
    
    def _format_plan_response(self, plan: dict) -> str:
        """格式化计划响应"""
        response = "📋 **学习计划已生成！**\n\n"
        response += f"**《{plan.get('title', '学习计划')}》**\n\n"
        response += f"📚 主题：{plan.get('subject', '通用')}\n"
        response += f"🎯 目标：{plan.get('target', '掌握知识')}\n"
        response += f"⏱️ 每日学习：{plan.get('daily_duration', 60)} 分钟\n"
        response += f"📆 总时长：{plan.get('total_days', 0)} 天\n\n"
        response += "**📖 学习阶段：**\n\n"
        
        phases = plan.get("phases", [])
        for i, phase in enumerate(phases, 1):
            response += f"{i}. **{phase.get('name', f'阶段{i}')}** ({phase.get('duration_days', 0)}天)\n"
            response += f"   📝 {phase.get('description', '')}\n"
            response += f"   🎯 目标：{', '.join(phase.get('goals', []))}\n\n"
        
        response += "**🏆 里程碑：**\n"
        for milestone in plan.get("milestones", []):
            response += f"- 第{milestone.get('day')}天：{milestone.get('description')}\n"
        
        response += "\n\n确认此计划吗？确认后我将为你创建详细的学习任务！"
        
        return response
