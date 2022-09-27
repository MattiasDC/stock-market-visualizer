import json

import dash
from dash import dcc
from dash_extensions.enrich import Input, Output, State
from httpx import URL

from stock_market_visualizer.app.config_store import ConfigStore


class RestoreableStateLayout:
    def __init__(self):
        self.location_id = "url"
        self.location = dcc.Location(id="url", refresh=False)
        self.restoreable_id = "restoreable-state"
        self.restoreable_state = dcc.Store(id="restoreable-state")

    def get_url(self):
        return "url", "href"

    def get_restoreable_state(self):
        return self.restoreable_id, "data"

    def get_layout(self):
        return [self.location, self.restoreable_state]

    def register_callbacks(self, app, redis):
        @app.callback(Output(*self.get_restoreable_state()), Input(*self.get_url()))
        def update_state_from_url(url):
            url_splitted = URL(url).path.split("/engine/")
            if len(url_splitted) < 2:
                return ConfigStore(redis).get(ConfigStore.DEFAULT_VIEW_CONFIG_KEY)
            return url_splitted[1]

        @app.callback(
            Output("header-title", "value"),
            Output("engine-id", "data"),
            Output("start-date-picker", "date"),
            Output("end-date-picker", "date"),
            Output("indicator-table", "data"),
            Output("show-ticker-table", "value"),
            Output("show-indicator-table", "value"),
            Output("show-signal-table", "value"),
            Input(*self.get_restoreable_state()),
        )
        def update_from_state(state_id):
            state_json = redis.get(state_id)
            if state_json is None:
                state = {}
            else:
                state = json.loads(state_json)
            keys = [
                "header-title",
                "engine-id",
                "start-date",
                "end-date",
                "indicators",
                "show-ticker-table",
                "show-indicator-table",
                "show-signal-table",
            ]
            return [
                state.get(key) if state.get(key) is not None else dash.no_update
                for key in keys
            ]

        @app.callback(
            Output("url-copy", "content"),
            Input("url-copy", "n_clicks"),
            State(*self.get_url()),
            State("header-title", "value"),
            State("engine-id", "data"),
            State("start-date-picker", "date"),
            State("end-date-picker", "date"),
            State("indicator-table", "data"),
            State("show-ticker-table", "value"),
            State("show-indicator-table", "value"),
            State("show-signal-table", "value"),
        )
        def create_url(
            n_clicks,
            url,
            header_title,
            engine_id,
            start_date,
            end_date,
            indicators,
            show_ticker_table,
            show_indicator_table,
            show_signal_table,
        ):
            if n_clicks == 0:
                return dash.no_update
            state_id = ConfigStore(redis).store_state(
                header_title,
                engine_id,
                start_date,
                end_date,
                indicators,
                show_ticker_table,
                show_indicator_table,
                show_signal_table,
            )
            url = URL(url)
            splitted_url = str(url).split("engine/")
            assert 0 < len(splitted_url) <= 2
            return f"{splitted_url[0]}engine/{state_id}"
