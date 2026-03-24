"""配置管理"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用
    APP_NAME: str = "AI学习规划师"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天
    
    # DashScope
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com"
    
    # 阿里云 OSS
    ALIYUN_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_OSS_BUCKET: str = "ai-study-planner"
    ALIYUN_OSS_ENDPOINT: str = "oss-cn-hangzhou.aliyuncs.com"
    
    # 阿里云短信
    ALIYUN_SMS_ACCESS_KEY_ID: Optional[str] = None
    ALIYUN_SMS_ACCESS_KEY_SECRET: Optional[str] = None
    ALIYUN_SMS_SIGN_NAME: str = "AI学习规划师"
    ALIYUN_SMS_TEMPLATE_CODE: str = "SMS_xxxxxxx"
    
    # 会员配置
    MONTHLY_TOKEN_QUOTA: int = 100000
    YEARLY_TOKEN_QUOTA: int = 1000000
    
    # 日志
    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
