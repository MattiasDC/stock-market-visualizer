import json
import uuid

import dash
from dash import dcc
from dash_extensions.enrich import Input, Output, State

from stock_market_visualizer.app.config import get_settings

FIXED_PATH = "/sme/"


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

    def register_callbacks(self, app, redis_getter):
        @app.callback(Output(*self.get_restoreable_state()), Input(*self.get_url()))
        def update_state_from_url(url):
            url_splitted = url.split(FIXED_PATH, 1)
            state_id = url_splitted[1]
            if len(state_id) == 0:
                return dash.no_update
            return state_id

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
            redis = redis_getter()
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
            url = url.split(FIXED_PATH, 1)[0]
            state = {}
            state["header-title"] = header_title
            state["engine-id"] = engine_id
            state["start-date"] = start_date
            state["end-date"] = end_date
            state["indicators"] = indicators
            state["show-ticker-table"] = show_ticker_table
            state["show-indicator-table"] = show_indicator_table
            state["show-signal-table"] = show_signal_table

            redis = redis_getter()
            state_id = str(uuid.uuid4())
            redis.set(
                state_id,
                json.dumps(state),
                get_settings().redis_restoreable_state_expiration_time,
            )

            return url + FIXED_PATH + state_id
