import datetime as dt
import os
from functools import cache

from pydantic import AnyUrl, BaseSettings
from simputils.logging import get_logger

logger = get_logger(__name__)


class Settings(BaseSettings):
    host_url: str = os.getenv("HOST_URL", "0.0.0.0")
    port: int = os.getenv("PORT", 8000)
    ssl_keyfile: str = os.getenv("SSL_KEYFILE")
    ssl_certfile: str = os.getenv("SSL_CERTFILE")
    api_url: AnyUrl = os.getenv("API_URL", "http://stock-market-engine")
    api_port: int = os.getenv("API_PORT", 8001)
    debug: bool = os.getenv("DEBUG", False)
    max_ticker_symbol_length: int = os.getenv("MAX_TICKER_SYMBOL_LENGTH", 10)
    update_interval: int = os.getenv("UPDATE_INTERVAL_SECONDS", 5 * 60)
    max_api_endpoint_cache_size: int = os.getenv("MAX_API_ENDPOINT_CACHE_SIZE", 10000)
    max_id_generator: int = os.getenv("MAX_ID_GENERATOR", 10000000)
    redis_url: str = os.getenv("REDIS_URL", "redis")
    redis_port: int = os.getenv("REDIS_PORT", 6379)
    redis_db: int = os.getenv("REDIS_DB")
    redis_restoreable_state_expiration_time: dt.timedelta = dt.timedelta(
        days=os.getenv("REDIS_RESTOREABLE_STATE_EXPIRATION_DAYS", 30)
    )
    default_engine_config: str = os.getenv("DEFAULT_ENGINE_CONFIG")
    default_view_config: str = os.getenv("DEFAULT_VIEW_CONFIG")
    title: str = os.getenv("TITLE", "Stock Market Engine")
    gtag: str = os.getenv("GTAG")


@cache
def get_settings() -> BaseSettings:
    logger.info("Loading config settings from the environment...")
    return Settings()
