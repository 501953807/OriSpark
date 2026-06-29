"""应用配置管理."""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从 .env 文件和环境变量加载."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用
    APP_NAME: str = "OriStudio"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-to-a-random-string"

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/oristudio.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # 服务器
    HOST: str = "127.0.0.1"
    PORT: int = 8765

    # CORS (开发时允许前端 dev server)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8765",
        "http://127.0.0.1:8765",
    ]

    # 工作区
    WORKSPACE_PATH: str = "~/OriStudio/workspace"

    # AES 加密密钥 (用于敏感字段加密)
    AES_KEY: Optional[str] = None

    # 外部 API (在设置页面配置)
    BANQUANJIA_API_KEY: Optional[str] = None
    BANQUANJIA_API_SECRET: Optional[str] = None
    ANTCHAIN_API_KEY: Optional[str] = None
    ANTCHAIN_API_SECRET: Optional[str] = None
    ZHIXINCHAIN_API_KEY: Optional[str] = None
    ZHIXINCHAIN_API_SECRET: Optional[str] = None
    BAIDU_VISION_API_KEY: Optional[str] = None
    GOOGLE_VISION_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"


settings = Settings()
