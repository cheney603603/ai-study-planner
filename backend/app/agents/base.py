"""Agent 基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.core.logging import get_logger
from app.core.dashscope import dashscope_client


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = get_logger(f"agents.{name}")
    
    @abstractmethod
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入，返回结果
        
        Args:
            context: 包含以下键的字典:
                - user_id: 用户ID
                - message: 用户消息
                - session_id: 会话ID
                - history: 历史消息
        
        Returns:
            包含以下键的字典:
                - response: Agent 响应文本
                - token_used: 消耗的 token 数
                - metadata: 额外的元数据
        """
        pass
    
    async def _call_llm(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        调用 LLM (DashScope)
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
        
        Returns:
            {"response": str, "token_used": int}
        """
        self.logger.info(f"调用 LLM: {prompt[:50]}...")
        
        try:
            result = await dashscope_client.simple_chat(
                prompt=prompt,
                system_prompt=system_prompt
            )
            return result
        except Exception as e:
            self.logger.error(f"LLM 调用失败: {str(e)}")
            raise
    
    async def _call_llm_with_messages(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        使用消息列表调用 LLM
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词
            temperature: 温度参数
        
        Returns:
            {"response": str, "token_used": int}
        """
        self.logger.info(f"调用 LLM (多轮对话): {len(messages)} 条消息")
        
        try:
            result = await dashscope_client.chat_completion(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature
            )
            return result
        except Exception as e:
            self.logger.error(f"LLM 调用失败: {str(e)}")
            raise
    
    def log(self, level: str, message: str, **kwargs):
        """日志记录"""
        extra = {"agent": self.name}
        extra.update(kwargs)
        getattr(self.logger, level)(message, extra=extra)
