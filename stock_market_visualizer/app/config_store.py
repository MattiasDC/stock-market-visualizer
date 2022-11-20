import datetime as dt
import json
import uuid

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


def configure_default_configs(api, redis, settings) -> None:
    engine_config = load_json_from_file(settings.default_engine_config)
    if engine_config is None:
        return None

    view_config = load_json_from_file(settings.default_view_config)
    engine_id = configure_default_engine(api, redis, engine_config, view_config)
    if engine_id is None:
        return None

    if view_config is None:
        return None
    configure_default_engine_view(engine_id, redis, engine_config, view_config)


def configure_default_engine(api, redis, engine_config, view_config) -> None:
    start_date = dt.datetime.now().date() - dt.timedelta(
        days=int(view_config["last_x_days"])
    )
    engine_config["stock_market"]["start_date"] = start_date.isoformat()

    for sd in engine_config["signal_detectors"]:
        sd["config"] = json.dumps(sd["config"])

    engine = api.create_engine_from_json(json.dumps(engine_config))
    end_date = dt.datetime.now().date().isoformat()
    engine = engine.update_engine(end_date)

    return engine.engine_id


def configure_default_engine_view(engine_id, redis, engine_config, view_config) -> None:
    start_date = engine_config["stock_market"]["start_date"]
    end_date = dt.datetime.now().date().isoformat()
    config_store = ConfigStore(redis)

    view_config_id = config_store.get(ConfigStore.DEFAULT_VIEW_CONFIG_KEY)
    if view_config_id is not None:
        default_config = config_store.get(view_config_id)
        if (
            default_config is not None
            and json.loads(default_config)["engine-id"] == engine_id
        ):
            return

    view_config["engine_id"] = str(engine_id)
    view_config["end_date"] = end_date

    def bool_to_list(value):
        return [True] if value else []

    view_config_id = config_store.store_state(
        view_config["header_title"],
        view_config["engine_id"],
        start_date,
        view_config["end_date"],
        view_config["indicators"],
        bool_to_list(view_config["show_ticker_table"]),
        bool_to_list(view_config["show_indicator_table"]),
        bool_to_list(view_config["show_signal_table"]),
    )
    config_store.set(ConfigStore.DEFAULT_VIEW_CONFIG_KEY, view_config_id)

    logger.info(f"(Re)configured default view config: {view_config_id}")
