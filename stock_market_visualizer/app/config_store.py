import datetime as dt
import json
import uuid
from http import HTTPStatus

import httpx
from simputils.logging import get_logger

from stock_market_visualizer.app.config import get_settings

logger = get_logger(__name__)


class ConfigStore:
    DEFAULT_VIEW_CONFIG_KEY = "DEFAULT_VIEW_CONFIG_ID"

    def __init__(self, redis):
        self.__redis = redis

    def get(self, key) -> str:
        value = self.__redis.get(key)
        if value is None:
            return None
        return value

    def set(self, key, value, *args) -> None:
        self.__redis.set(key, value, *args)

    def store_state(
        self,
        header_title,
        engine_id,
        start_date,
        end_date,
        indicators,
        show_ticker_table,
        show_indicator_table,
        show_signal_table,
    ) -> str:
        state = {}
        state["header-title"] = header_title
        state["engine-id"] = engine_id
        state["start-date"] = start_date
        state["end-date"] = end_date
        state["indicators"] = indicators
        state["show-ticker-table"] = show_ticker_table
        state["show-indicator-table"] = show_indicator_table
        state["show-signal-table"] = show_signal_table

        state_id = str(uuid.uuid4())
        self.set(
            state_id,
            json.dumps(state),
            get_settings().redis_restoreable_state_expiration_time,
        )
        return state_id


def load_json_from_file(file_path):
    if file_path is None:
        return None
    config = None
    with open(file_path) as f:
        config = json.load(f)
    return config


async def configure_default_configs(redis, settings) -> None:
    engine_config = load_json_from_file(settings.default_engine_config)
    if engine_config is None:
        return None

    view_config = load_json_from_file(settings.default_view_config)
    engine_id = await configure_default_engine(
        redis, settings, engine_config, view_config
    )
    if engine_id is None:
        return None

    if view_config is None:
        return None
    configure_default_engine_view(engine_id, redis, engine_config, view_config)


async def configure_default_engine(redis, settings, engine_config, view_config) -> None:
    start_date = dt.datetime.now().date() - dt.timedelta(
        days=int(view_config["last_x_days"])
    )
    engine_config["stock_market"]["start_date"] = start_date.isoformat()

    for sd in engine_config["signal_detectors"]:
        sd["config"] = json.dumps(sd["config"])

    sme_backend_url = f"{settings.api_url}:{settings.api_port}"
    client = httpx.AsyncClient(base_url=sme_backend_url)
    response = await client.post(url="/create", json=engine_config)
    if response.status_code != HTTPStatus.OK:
        logger.error(f"Error during creation of default engine: {response.text}")
        return None

    engine_id = response.json()
    logger.info(f"Configured default engine: {engine_id}")
    return engine_id


def configure_default_engine_view(engine_id, redis, engine_config, view_config) -> None:
    view_config["engine_id"] = str(engine_id)
    view_config["end_date"] = dt.datetime.now().date().isoformat()

    def bool_to_list(value):
        return [True] if value else []

    config_store = ConfigStore(redis)
    view_config_id = config_store.store_state(
        view_config["header_title"],
        view_config["engine_id"],
        engine_config["stock_market"]["start_date"],
        view_config["end_date"],
        [],
        bool_to_list(view_config["show_ticker_table"]),
        bool_to_list(view_config["show_indicator_table"]),
        bool_to_list(view_config["show_signal_table"]),
    )
    config_store.set(ConfigStore.DEFAULT_VIEW_CONFIG_KEY, view_config_id)

    logger.info(f"Configured default config: {view_config_id}")
