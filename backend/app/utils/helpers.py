"""工具函数"""
from datetime import datetime, timedelta
from typing import Optional
import uuid


def generate_uuid() -> str:
    """生成 UUID"""
    return str(uuid.uuid4())


def get_today_start() -> datetime:
    """获取今天开始时间"""
    return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


def get_week_start() -> datetime:
    """获取本周开始时间（周一）"""
    today = datetime.utcnow()
    return today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=today.weekday())


def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M") -> Optional[str]:
    """格式化日期时间"""
    if not dt:
        return None
    return dt.strftime(fmt)
