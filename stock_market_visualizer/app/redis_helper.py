import redis
from simputils.logging import get_logger

from stock_market_visualizer.app.config import Settings

logger = get_logger(__name__)
global_settings = Settings()


def init_redis_pool():
    r = redis.from_url(
        url="redis://" + global_settings.redis_url,
        port=global_settings.redis_port,
        encoding="utf-8",
        db=global_settings.redis_db,
        decode_responses=True,
    )
    logger.info("Initialized sync redis")
    return r
