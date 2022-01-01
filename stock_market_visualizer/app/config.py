import datetime as dt
import os
from functools import cache
from pydantic import AnyUrl, BaseSettings
from utils.logging import get_logger

logger = get_logger(__name__)

class Settings(BaseSettings):
    host_url: str = os.environ.get("HOST_URL", "0.0.0.0")
    port: int = os.environ.get("PORT", 8000)
    ssl_keyfile: str = os.environ.get("SSL_KEYFILE", "0.0.0.0-key.pem")
    ssl_certfile: str = os.environ.get("SSL_KEYFILE", "0.0.0.0.pem")
    api_url: AnyUrl = os.getenv("API_URL", "http://sme-api-smv")
    api_port: int = os.getenv("API_PORT", 8001)
    debug: bool = os.getenv("DEBUG", False)
    max_ticker_symbol_length : int = os.getenv("MAX_TICKER_SYMBOL_LENGTH", 10)
    update_interval: int = os.getenv("UPDATE_INTERVAL_SECONDS", 5*60)
    max_api_endpoint_cache_size: int = os.getenv("MAX_API_ENDPOINT_CACHE_SIZE", 20000)
    max_id_generator: int = os.getenv("MAX_ID_GENERATOR", 10000000)
    redis_url: AnyUrl = os.environ.get("REDIS_URL", "redis://redis")
    redis_port: int = os.getenv("REDIS_PORT", 6379)
    redis_db: int = os.getenv("REDIS_DB", 0)
    redis_restoreable_state_expiration_time : dt.timedelta =\
        dt.timedelta(days=os.getenv("REDIS_RESTOREABLE_STATE_EXPIRATION_DAYS", 30))

@cache
def get_settings() -> BaseSettings:
    logger.info("Loading config settings from the environment...")
    return Settings()