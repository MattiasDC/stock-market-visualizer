import os
from functools import cache
from pydantic import AnyUrl, BaseSettings
from stock_market_visualizer.common.logging import get_logger

logger = get_logger(__name__)

class Settings(BaseSettings):
    host_url: str = os.environ.get("HOST_URL", "0.0.0.0")
    port: int = os.environ.get("PORT", 8000)
    redis_url: AnyUrl = os.environ.get("REDIS_URL", "redis://redis")
    redis_port: int = os.getenv("REDIS_PORT", 6379)
    redis_db: int = os.getenv("REDIS_DB", 0)
    debug: bool = os.getenv("DEBUG", False)

@cache
def get_settings() -> BaseSettings:
    logger.info("Loading config settings from the environment...")
    return Settings()