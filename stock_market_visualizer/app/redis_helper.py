from redis import from_url
from utils.logging import get_logger

from stock_market_visualizer.app.config import Settings

logger = get_logger(__name__)
global_settings = Settings()


def init_redis_pool():
    redis = from_url(
        global_settings.redis_url,
        encoding="utf-8",
        db=global_settings.redis_db,
        decode_responses=True,
    )
    logger.info("Initialized redis")
    return redis
