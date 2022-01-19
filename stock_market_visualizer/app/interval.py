import datetime as dt

from dash import dcc

from stock_market_visualizer.app.config import get_settings


class IntervalLayout:
    def __init__(self):
        self.interval = "update-interval"
        self.layout = dcc.Interval(
            id=self.interval,
            interval=dt.timedelta(
                seconds=get_settings().update_interval
            ).total_seconds()
            * 1000,  # milliseconds
            n_intervals=0,
        )

    def get_interval(self):
        return self.interval, "n_intervals"

    def get_layout(self):
        return self.layout
