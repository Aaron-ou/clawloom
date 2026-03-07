# WorldSeed Engine Configuration

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 数据库
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/clawloom"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # OpenClaw API
    OPENCLAW_URL: str = "http://localhost:8080"
    OPENCLAW_API_KEY: Optional[str] = None
    
    # 引擎配置
    DEFAULT_TICKS_PER_BATCH: int = 10
    MAX_TICKS_PER_BATCH: int = 100
    TICK_DELAY_SECONDS: float = 0.1  # tick之间的延迟，避免API限流
    
    # 日志
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 冲突仲裁
    CONFLICT_RESOLUTION_RANDOMNESS: float = 0.2  # 随机因素权重
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()
