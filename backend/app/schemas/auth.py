"""认证相关模型"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re

# 中国大陆手机号正则（1 开头，第二位 3-9，共 11 位）
_CN_PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    phone: str = Field(..., description="手机号（中国大陆 11 位）")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not _CN_PHONE_RE.match(v):
            raise ValueError("手机号格式不正确，请输入 11 位中国大陆手机号")
        return v


class SendCodeResponse(BaseModel):
    """发送验证码响应"""
    code: str = "success"
    message: str = "验证码已发送"
    expire_seconds: int = 300  # 验证码有效期


class LoginRequest(BaseModel):
    """登录请求"""
    phone: str = Field(..., description="手机号")
    code: str = Field(..., min_length=6, max_length=6, description="6 位验证码")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not _CN_PHONE_RE.match(v):
            raise ValueError("手机号格式不正确")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("验证码必须为 6 位数字")
        return v


class LoginResponse(BaseModel):
    """登录响应"""
    code: str = "success"
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 有效期（秒）
    user: Optional["UserInfo"] = None


class UserInfo(BaseModel):
    """用户信息"""
    id: str
    phone: str
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    level: str = "入门"
    total_score: int = 0
    
    class Config:
        from_attributes = True


class TokenUsage(BaseModel):
    """Token 用量"""
    quota: int  # 配额
    used: int  # 已用
    remaining: int  # 剩余
    reset_date: Optional[str] = None  # 重置日期
