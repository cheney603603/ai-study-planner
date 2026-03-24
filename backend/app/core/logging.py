"""结构化日志系统"""
import sys
import logging
from pathlib import Path
from datetime import datetime
from loguru import logger
from app.config import settings


def setup_logging():
    """初始化日志系统"""
    # 确保日志目录存在
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 移除默认 handler
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        colorize=True
    )
    
    # 应用日志文件
    logger.add(
        log_dir / "app.log",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8"
    )
    
    # Agent 日志文件
    logger.add(
        log_dir / "agents.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8"
    )
    
    # API 日志文件
    logger.add(
        log_dir / "api.log",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8"
    )
    
    # 错误日志文件
    logger.add(
        log_dir / "error.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
        encoding="utf-8"
    )
    
    logger.info(f"日志系统初始化完成，日志目录: {log_dir.absolute()}")


def get_logger(name: str = "app") -> logger:
    """获取日志器"""
    return logger.bind(name=name)
