"""DashScope API 客户端"""
import json
import httpx
from typing import Optional, Dict, Any, List
from app.core.logging import get_logger
from app.config import settings

logger = get_logger("core.dashscope")


class DashScopeClient:
    """DashScope API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.DASHSCOPE_API_KEY
        self.base_url = settings.DASHSCOPE_BASE_URL
        self.model = settings.DASHSCOPE_MODEL
        self.logger = get_logger("core.dashscope")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        调用 DashScope API 进行对话补全
        
        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            {"response": str, "token_used": int}
        """
        if not self.api_key:
            raise ValueError("DashScope API Key 未配置")
        
        # 构建完整的消息列表
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": {
                "messages": full_messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message"
            }
        }
        
        self.logger.info(f"调用 DashScope API: model={self.model}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    self.logger.error(f"API 调用失败: {response.status_code} - {response.text}")
                    raise Exception(f"API 调用失败: {response.status_code}")
                
                result = response.json()
                
                # 解析响应
                output = result.get("output", {})
                choices = output.get("choices", [])
                
                if not choices:
                    raise Exception("API 返回格式错误：缺少 choices")
                
                message = choices[0].get("message", {})
                content = message.get("content", "")
                
                # 计算 token 使用量
                usage = result.get("usage", {})
                token_used = usage.get("total_tokens", 0)
                
                self.logger.info(f"API 调用成功: token_used={token_used}")
                
                return {
                    "response": content,
                    "token_used": token_used,
                    "finish_reason": choices[0].get("finish_reason", "")
                }
                
        except httpx.TimeoutException:
            self.logger.error("API 调用超时")
            raise Exception("AI 服务响应超时，请稍后重试")
        except httpx.HTTPError as e:
            self.logger.error(f"API 调用错误: {str(e)}")
            raise Exception(f"AI 服务调用失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"API 调用异常: {str(e)}")
            raise
    
    async def simple_chat(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        简单的单轮对话
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
        
        Returns:
            {"response": str, "token_used": int}
        """
        return await self.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt
        )


# 全局客户端实例
dashscope_client = DashScopeClient()
