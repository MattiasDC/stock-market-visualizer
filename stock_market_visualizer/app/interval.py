import datetime as dt

import dash
from dash import dcc
from dash_extensions.enrich import Input, Output, State
from utils.dateutils import from_sdate
from utils.logging import get_logger

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.config import get_settings

logger = get_logger(__name__)


class IntervalLayout:
    def __init__(self, engine_layout, date_layout):
        self.interval = "update-interval"
        self.layout = dcc.Interval(
            id=self.interval,
            interval=dt.timedelta(
                seconds=get_settings().update_interval
            ).total_seconds()
            * 1000,  # milliseconds
            n_intervals=0,
        )
        self.engine_layout = engine_layout
        self.date_layout = date_layout

    def get_interval(self):
        return self.interval, "n_intervals"

    def get_layout(self):
        return self.layout

    def register_callbacks(self, app, client_getter):
        @app.callback(
            Output(*self.engine_layout.get_id()),
            Input(*self.get_interval()),
            State(*self.date_layout.get_end_date()),
            State(*self.engine_layout.get_id()),
            State("indicator-table", "data"),
        )
        def update_on_interval(n_intervals, end_date, engine_id, indicator_rows):
            end_date = from_sdate(end_date)
            now = dt.datetime.now()
            # We still want to update on interval if we just crossed a day
            if end_date is None or now - dt.datetime.combine(
                end_date, dt.time()
            ) > dt.timedelta(days=1, minutes=1, seconds=get_settings().update_interval):
                return dash.no_update

            logger.info("Interval callback triggered: updating engine")
            client = client_getter()
            new_engine_id = api.update_engine(engine_id, end_date, client)
            return new_engine_id
